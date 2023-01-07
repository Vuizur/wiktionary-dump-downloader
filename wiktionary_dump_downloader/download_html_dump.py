from typing import Literal
import requests
import bs4
import tarfile

HTML_DUMP_URL = "https://dumps.wikimedia.org/other/enterprise_html/runs/"

DumpType = Literal[
    "wiki",
    "wiktionary",
    "wikibooks",
    "wikinews",
    "wikisource",
    "wikiquote",
    "wikiversity",
    "wikivoyage",
]

class HtmlDumpDownloader:
    def __init__(
        self,
        lang_code: str,
        dump_type: DumpType,
        output_folder: str,
        namespace: int = 0,
    ) -> None:
        """Downloads the HTML dump of the given language and type."""
        response = requests.get(HTML_DUMP_URL)
        response.raise_for_status()
        soup = bs4.BeautifulSoup(response.text, "html.parser")
        # Find the last link
        link = soup.find_all("a")[-1]
        link_to_latest_dump = HTML_DUMP_URL + link["href"]
        response = requests.get(link_to_latest_dump)
        response.raise_for_status()
        soup = bs4.BeautifulSoup(response.text, "html.parser")

        # Put all the links in a list
        links = []
        for link in soup.find_all("a"):
            links.append(link["href"])

        results = []
        # Find the link to the dump of the given language and type
        for link in links:
            # Check if the link starts with the language code
            if (
                link.startswith(lang_code + dump_type)
                and f"NS{namespace}" in link
                and "ENTERPRISE-STATS.json" not in link
            ):
                results.append(link)

        if len(results) == 0:
            print(
                "No dumps found for the given language and type. Please check the language code and dump type."
            )

        elif len(results) > 1:
            print(results)
            raise Exception(
                "Multiple dumps found for the given language and type. This should not happen. Please report this issue on GitHub."
            )

        print(f"Downloading {results[0]}...")
        response = requests.get(link_to_latest_dump + results[0])
        response.raise_for_status()
        with open(results[0], "wb") as f:
            f.write(response.content)
        print(f"Downloaded {results[0]}")

        self._output_folder = output_folder
        self._lang_code = lang_code
        self._dump_type = dump_type
        self._namespace = namespace
        self.packed_dump_path = results[0]

    def unpack_dump(self):
        """Unpacks the dump and yields the single files. Use this if you don't want to unpack the whole dump at once
        (for example for space reasons)."""
        with tarfile.open(self.packed_dump_path) as tar:
            for member in tar.getmembers():
                f = tar.extractfile(member)
                if f is not None:
                    yield f.read()

    def delete_dump(self):
        import os

        os.remove(self.packed_dump_path)