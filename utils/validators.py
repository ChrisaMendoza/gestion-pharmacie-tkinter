from datetime import date

def validate_medicament(data):
    if not data.get("code") or not data.get("nom_commercial"):
        raise ValueError("Code et nom commercial obligatoires")

    try:
        prix = float(data.get("prix_vente"))
        if prix <= 0:
            raise ValueError
    except:
        raise ValueError("Prix de vente invalide")

    if data.get("date_peremption"):
        if data["date_peremption"] <= str(date.today()):
            raise ValueError("Date de péremption invalide")
