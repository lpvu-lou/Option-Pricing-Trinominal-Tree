import datetime as dt

def datetime_to_years(date_value, ref_date):
    """
    Convertit une date (ou une liste de dates) en temps (float, années)
    """
    if date_value is None:
        return None

    # Si c'est une liste de dates
    if isinstance(date_value, list):
        return [datetime_to_years(d, ref_date) for d in date_value]

    # Si c'est une seule date
    if isinstance(date_value, dt.datetime) and isinstance(ref_date, dt.datetime):
        return (date_value - ref_date).days / 365.0

    # Si c'est déjà un float
    if isinstance(date_value, (int, float)):
        return float(date_value)

    raise TypeError(f"Invalid type for date conversion: {type(date_value)} (value={date_value})")
