#currency exchange API and date-time API function helpers for toll calling
import requests
import datetime
def get_exchange_rate(base_currency, target_currency):
    # normalise input: the API expects uppercase currency codes
    base = base_currency.upper()
    target = target_currency.upper()
    url=f"https://open.er-api.com/v6/latest/{base}"
    # timeout stops the call hanging forever; without it a slow server freezes the chat
    response=requests.get(url,timeout=10)
    # raises requests.HTTPError for 4xx/5xx responses, so failures aren't silent
    response.raise_for_status()
    data = response.json()
    # API-level failure (for example an unknown base currency): raise instead of returning None
    if data.get("result") != "success":
        raise ValueError(f"Exchange rate API returned an error for base {base}.")
    rate=data["rates"].get(target)  # .get() returns None if the target code doesn't exist
    if rate is None:
        raise ValueError(f"Exchange rate for {target} not found.")

    # return context along with the number, so the model can phrase a correct answer
    return {"base": base, "target": target, "rate": rate}    

def get_current_datetime():
    # current time with the system's local timezone attached (IST on your machine)
    now=datetime.datetime.now().astimezone()
    # return labelled fields so the model can answer "what day is it?" correctly
    return {
        "date": now.strftime("%Y-%m-%d"),     # for example 2026-10-13
        "time": now.strftime("%H:%M:%S"),     # 24-hour clock
        "weekday": now.strftime("%A"),        # for example Tuesday
        "timezone": now.strftime("%Z"),       # timezone name; check what this prints on Windows
    }

if __name__ == "__main__":
    print(get_exchange_rate("usd", "inr"))     # lowercase on purpose, to check normalisation
    print(get_current_datetime())
    # also try a bad currency and see the error message you get:
    # print(get_exchange_rate("USD", "XYZ"))