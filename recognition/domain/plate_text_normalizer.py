class PlateTextNormalizer:
    def normalize(self, raw_text: str) -> str:
        cleaned = "".join(char for char in raw_text if char.isalnum())
        cleaned = cleaned.upper()
        if len(cleaned) != 7:
            return ""
        return cleaned
