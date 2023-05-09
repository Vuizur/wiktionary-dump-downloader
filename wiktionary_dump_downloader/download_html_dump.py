import json
from typing import Literal
import requests
import bs4
import tarfile
import os
import pySmartDL

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
            print("Checking for local files...")
            # Check if there are any local files that match the given language and type
            for file in os.listdir(""):
                if (
                    file.startswith(lang_code + dump_type)
                    and f"NS{namespace}" in file
                ):
                    results.append(file)


        elif len(results) > 1:
            print(results)
            raise Exception(
                "Multiple dumps found for the given language and type. This should not happen. Please report this issue on GitHub."
            )

        # Check if the dump is already downloaded
        elif os.path.exists(results[0]):
            print(
                f"The dump {results[0]} is already downloaded. If you want to download it again, please delete it first."
            )
        else:
            print(f"Downloading {results[0]}...")
            #download_file_fast(link_to_latest_dump + results[0], results[0])

            url = link_to_latest_dump + results[0]
            dest = "" #results[0]
            obj = pySmartDL.SmartDL(url, dest)
            obj.start()

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
                #f = tar.extractfile(member)
                # Write member to file
                print("Extracting member " + member.name)
                tar.extract(member)
                with open(member.name, "r", encoding="utf-8") as f:
                    for line in f:
                        yield line
                os.remove(member.name)

    def delete_dump(self):
        import os

        os.remove(self.packed_dump_path)

if __name__ == "__main__":
    downloader = HtmlDumpDownloader("cs", "wikiquote", "test-output")
    for i, line in enumerate(downloader.unpack_dump()):
        # convert the bytes to a string
        line = json.loads(line)
        print(line)
        if i == 10:
            break