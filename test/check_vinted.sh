#!/bin/bash
ITEM="https://www.vinted.fr/items/922704975-adidas-x-15"
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

echo "Minimal curl:"
curl -s -o /dev/null -w "%{http_code}\n" "$ITEM"

echo "With UA:"
curl -s -A "$UA" -o /dev/null -w "%{http_code}\n" "$ITEM"

echo "With UA + headers:"
curl -s --http2 -A "$UA" -H "Accept-Language: en-GB,en;q=0.9" -H "Referer: https://www.vinted.fr/" -o /dev/null -w "%{http_code}\n" "$ITEM"

echo "With cookie jar (warm catalog first):"
touch cookies.txt
curl -s -L --cookie ./cookies.txt --cookie-jar ./cookies.txt -A "$UA" "https://www.vinted.fr/catalog?search_text=adidas" >/dev/null
curl -s -L --cookie ./cookies.txt --cookie-jar ./cookies.txt -A "$UA" -o /dev/null -w "%{http_code}\n" "$ITEM"

echo "Your public IP:"
curl -s https://api.ipify.org ; echo
