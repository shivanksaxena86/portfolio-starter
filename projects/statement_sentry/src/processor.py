import os

import pikepdf
from config import CARD_CONFIG


def get_card_key_from_filename(filename):
    """
    Mapping filenames to our CARD_CONFIG keys based on keywords.
    """
    fname = filename.upper()
    if "AMAZON" in fname:
        return "ICICI_AMAZON"
    if "SAPPHIRO" in fname:
        return "ICICI_SAPPHIRE"
    if "CORAL" in fname:
        return "ICICI_CORAL"  # We should add this to config
    if "5522" in fname or "REGALIA" in fname:
        return "HDFC_REGALIA"
    if "6529" in fname or "TATA" in fname:
        return "HDFC_TATA_NEU"
    if "500089" in fname or "YES" in fname:
        return "YES_BANK"
    return None


def unlock_pdfs():
    raw_dir = "projects/statement_sentry/data/raw_pdfs"
    decrypted_dir = "projects/statement_sentry/data/decrypted_pdfs"
    os.makedirs(decrypted_dir, exist_ok=True)

    for filename in os.listdir(raw_dir):
        if not filename.endswith(".pdf"):
            continue

        print(f"\n--- Processing: {filename} ---")

        # New smarter matching
        card_key = get_card_key_from_filename(filename)
        matched_config = CARD_CONFIG.get(card_key) if card_key else None

        if not matched_config:
            print("Skipping: No matching card config found for this filename pattern.")
            continue

        input_path = os.path.join(raw_dir, filename)
        # Clean up output filename for better readability
        output_filename = f"unlocked_{card_key}_{filename.split('_')[-1]}"
        output_path = os.path.join(decrypted_dir, output_filename)

        success = False
        for password in matched_config.get("passwords", []):
            try:
                # We use 'allow_overwriting_input=True' just in case,
                # but we are saving to a new folder anyway.
                with pikepdf.open(input_path, password=password) as pdf:
                    pdf.save(output_path)
                    print(f"✅ Success! Unlocked as: {output_filename}")
                    success = True
                    break
            except pikepdf.PasswordError:
                print(f"❌ Password '{password}' failed.")
                continue
            except Exception as e:
                print(f"⚠️ Unexpected error: {e}")
                break

        if not success:
            print(f"🛑 Could not unlock {filename}. Check passwords in config.py")


if __name__ == "__main__":
    unlock_pdfs()
