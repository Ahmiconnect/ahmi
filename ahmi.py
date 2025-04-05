#ahmi.py

class AnimeVideoNamer:
    def __init__(self):
        self.associations = {
            "luffy": "onepiece",
            "naruto": "narutoshippuden",
            "saitama": "opm",
            "goku": "dbz",
            "ichigo": "bleach",
            "gojo": "jjk",
            "madara": "naruto",
            "sukuna": "jjk",
            "kakashi": "naruto",
            "vegeta": "dragonball"
        }


    def create_title(self, entries: list[dict], for_filename: bool = False) -> str:
        seen_folders = []
        hashtags = {"#animebattle"}

        for entry in entries:
            folder = entry["Folder"].lower()
            if folder not in seen_folders:
                seen_folders.append(folder)
                assoc_word = self.associations.get(folder)
                if assoc_word:
                    hashtags.add(f"#{assoc_word} #{folder}")

        title_main = " vs ".join(seen_folders)
        hashtags_str = " ".join(sorted(hashtags))  # optional: sorted for consistency
        
        full_title = f"{title_main} {hashtags_str}"
        if for_filename:
            return full_title.replace("_", "#")
        return full_title