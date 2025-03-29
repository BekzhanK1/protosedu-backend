import secrets

import re

from django.template.loader import render_to_string
from django.utils.html import strip_tags


def render_email(first_name, last_name, current_cups, level, dashboard_url):
    context = {
        "first_name": first_name,
        "last_name": last_name,
        "current_cups": current_cups,
        "level": level,
        "dashboard_url": dashboard_url,
    }
    html_content = render_to_string("daily_email.html", context)
    text_content = strip_tags(html_content)
    return html_content, text_content


def generate_password():
    password_length = 8
    return secrets.token_urlsafe(password_length)


import boto3
from botocore.exceptions import NoCredentialsError


def get_presigned_url(bucket_name, key, expiration=3600):
    s3_client = boto3.client("s3", region_name="eu-north-1")
    try:
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": key},
            ExpiresIn=expiration,
        )
        return url
    except NoCredentialsError:
        return None
    except Exception as e:
        return None


def cyrillic_to_username(text):
    translit_map = {
        "А": "A",
        "Ә": "A",
        "Б": "B",
        "В": "V",
        "Г": "G",
        "Ғ": "G",
        "Д": "D",
        "Е": "E",
        "Ё": "Yo",
        "Ж": "Zh",
        "З": "Z",
        "И": "I",
        "Й": "Y",
        "К": "K",
        "Қ": "Q",
        "Л": "L",
        "М": "M",
        "Н": "N",
        "Ң": "N",
        "О": "O",
        "Ө": "O",
        "П": "P",
        "Р": "R",
        "С": "S",
        "Т": "T",
        "У": "U",
        "Ұ": "U",
        "Ү": "U",
        "Ф": "F",
        "Х": "Kh",
        "Һ": "H",
        "Ц": "Ts",
        "Ч": "Ch",
        "Ш": "Sh",
        "Щ": "Shch",
        "Ъ": "",
        "Ы": "Y",
        "І": "I",
        "Ь": "",
        "Э": "E",
        "Ю": "Yu",
        "Я": "Ya",
        "а": "a",
        "ә": "a",
        "б": "b",
        "в": "v",
        "г": "g",
        "ғ": "g",
        "д": "d",
        "е": "e",
        "ё": "yo",
        "ж": "zh",
        "з": "z",
        "и": "i",
        "й": "y",
        "к": "k",
        "қ": "q",
        "л": "l",
        "м": "m",
        "н": "n",
        "ң": "n",
        "о": "o",
        "ө": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ұ": "u",
        "ү": "u",
        "ф": "f",
        "х": "kh",
        "һ": "h",
        "ц": "ts",
        "ч": "ch",
        "ш": "sh",
        "щ": "shch",
        "ъ": "",
        "ы": "y",
        "і": "i",
        "ь": "",
        "э": "e",
        "ю": "yu",
        "я": "ya",
    }

    latin_text = "".join(translit_map.get(char, char) for char in text)

    latin_text = re.sub(r"[^a-zA-Z0-9_]", ".", latin_text)

    return latin_text.lower()


def get_cache_key(prefix, user, child_id=None, **kwargs):
    key = f"{prefix}_user_{user.id}"
    if child_id:
        key += f"_child_{child_id}"
    for k, v in kwargs.items():
        key += f"_{k}_{v}"
    print("[get_cache_key]", key)
    return key
