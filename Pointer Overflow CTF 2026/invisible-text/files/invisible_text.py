#!/usr/bin/env python3   	 	    
"""	
diary_reader.py     	  				
	
Reads a diary entry preserved in the DR3 archive format.     	    		
Version 3 archives store the payload as concatenated	
base64 chunks over a zlib-compressed stream.     	 	 	  
"""	
import base64     	   		 
import zlib	
     				 		
_VERSION = 3	
_ARCHIVE_ID = "DR-2026-0342"     	 	    
_ENCODING = "utf-8"	
     	  	  	
# Payload — recovered from backup tape, split into fixed	
# chunks by the DR3 reader; reassembled by _reconstruct().     	   	 	
_CHUNKS = [	
    "eNrVWNtuGzcQfd+vti5JJVdJVoKaCKhhkVwnUV4qO0q6KFzJ/8Iv6cyZC0kl6FNf",     	  		 	
    "CgjCiuLuzuXMmTPMYZ2HaQ4xB/re5uEmh5RD//+5mHc57nK6yWma4zKHR75mZz7m",	
    "QBev4duc/71a+a/2yEqCNWnCK/Ff99BKuvpr1eUQcpjhlas8TPRZ6tKc/4or2033",     	 	    
    "3+J7gW9aWeaIPXQv//T9MQ8/26MmvtLnyF2xZ29pT5pxECnAMTR3RbydH4V7+Qn0",	
    "qE2O9IoHMobyQG4NOVA2At/P37d4WW929DCaXjPhANB6hKv8dNmPBIaF+kDPDRNY",     	     	
    "gNewiSEnSbL8XJnd8Cq49QhwimwGv1c8kVeID3f6NMb/ArfQkyeSh8ir/tC00ngw",	
    "4MxdcjJ6EnvNGMcjwCZJ0Qrb6AkDwhm5wMg3cZ4exc+B9eEb/u3xcInFlP0U3xQR",     	  				
    "qM84EcCwYVy3j4BcrKAx7Thm9ILBi+E2J4Nygg8aBjF9oRgQf9gCAkbiEHDI57x5",	
    "oM9DHnZ5+JaHT3n4iIuveSDLtmw6bWPLXlfhFGfmwMbSgi34fGQLk6Tuhu/inVv+",     	 	  		
    "TlPxsINbG7UpHTROnJBeHQ0WhrJtauGJTAm0OFAUnvLwPQ8v/In4Hp7zsC8Xspjo",	
    "e8zDJQ9zpE7CSSjfALFAlFRCchuWGp2wVJDzIkLPi5OuQshOveekW1UVvrLaCAdO",     	  		 	
    "FEfF3GCDxGgx9JLjGT/PsP4eRstftHKEG/LXMQ/vYcAt7I4Wtbkxiq07xjx8vEEK",	
    "j3lJEEJuvTXOEZei5cRrDmgRblb3vsGaF1izhzNk64iVEy9GWE8+pKMmJF1g/Rkr",     	  	   
    "e3U+vFeeSFJmFk0G8A3ebl7xda91pQ73HbA+Vy7iHbW7s8YT4Rx+zYmDR3cV5FzY",	
    "rHjRAKexOKO2HuGJ4+qiiUpyMcLKNcxat1X3tqKWrRKdWq82d2WrbxJK9sCrJ7hQ",     	   	  
    "AokcueHvysRRUyGAYVvvC5ySZUlQFC/llrJzRAGQcU9qNKUiVrVaqFniiCoC2Dpw",	
    "1qRweYInQrj8iK2Rw6JkMN7ndKcFoCUroAdIvCp0vUaRo+to+ys3iB4ISJSNMLcm",     	  		  
    "2GsxpEXpTtIo09LDinqItUCYWQ+yCg7z0rYFmvRTkqA1cK7MNU+0Ks5aGMWxs2aD",	
    "XTI3JBbxF/DMmllRAseGeuAf2xYspfuAelBs7RpEsfcgYEUXMhAPyhWcOuMipqB7",     	   	 	
    "s2MssGErx6rWvU6O5oxUxVgV+gf03Zl1qo2Z1Ju5wq0rDq4kBMYbt3IGzeO4kx5u",	
    "FNSXYuAKecVA1FIeDUuCcgGGo9/r+GygfzbmFdMlBAY2uhDQctOcqC6K1v4GF2wi",     	   			
    "qIROxQex0ns+rz5wQpM3dggV8opLzUhWKNXhoYA+l6g785Bx0VeMZNX0ve2R2z/A",	
    "uJ0R98TkUzC5ikKvCZe7GfsguA8qUbR3QDtITr2b8LfkYWVNTQDzXKHlRyyNmhyN",     	 	  	 
    "ektZdK2Vc0E9TBQ8it6FCp+41myo6beiWAUyXYUTgMrlN6dlYtmgv75gzPBmd6du",	
    "FN6EM7Gu4xcA3VOx196nRDSWnq2dRFrbW5Obwi6haGqN5s5KdCLg7+x3ULGlHOVA",     	 	 	  
    "BLcmd2yqEwn7/BcscN7cW72KoBgN6CdbfLakSU4uSsRCDyyQZojrqmg+VT0G7OLb",	
    "YzE4TDsrkbUWShRF1Jdr13kqkqVCRHu+y+HZcHVvPjhjjlVZ163DsQRqCvsiAlRB",     					 	
    "rHTMUM4U/ReM/Vcm5qNpPteApYZcrkgMgjGvzz0H3PWEwpDZ9U2Ov7M/4YWDrZ4c",	
    "DWxV9dMG/ux5M9P/xIL9xmKcLIKHRjsnc0wTsjCzF502Rf7bm7H1CrdeWWLDuZI8",  
    "yJgmo4WGTVUk3vcGgnyJsRaUwvPJEjMDleyszD1Cl8rj1Tys09XaoL4ufJrc7ZX1",
    "B7Fb63WnuPJ26Byn3aevOEpGXgRm6FH3SDpVXtrwy2Sa5dckTAtLhEbUyhPa1hxj",
    "QyWHyqEEZkMfHn1AlbOMZKKQo7ntmnrVAfcJg4jDsUqcSA/mByQkPsLWLea1P4CW",
    "P5sxSIseF9GueQ99PsPzT3gyufoKpm9soJshQGvlpRL1eTOZoVd0zYQgs6hojdS3",
    "jwOjqTokr95hwjSLlZ2OlUZymT1Wsm8sqkSJWOrkN8i4L5XwAUMmV/tyLFKN9X7s",
    "wmcz2gEWpYCkn8upiWYtqOoixzjk52p2e1Z+1CbtXHRsx7f7pmOoUpJ/j/aokWdu",
    "mqs4alvEeIoS8sOYoMUAOsIxxwK6NfmEUSNyVjV8GfnvMey/NNZfNel6SPCou4Ly",
    "hGjjc63uOXFnPkMdIfkU+yKZq1MLEXXg+k5bd5pXGmlRqcIHDCUHE9ut9RrjizZm",
    "7VxVT/Bx52oWbSRt1QRLz5a0kJUnrkztS6mIujTXWsXZzMKOlW7t8EIOyw56FqKR",
    "9ho9Fa1a5PRY9Wm3+NR08Tg2ZaPZOFWj37lM2wqzzwDVryAlOSPcVAccK6Giuh6m",
    "VWsUKuiRAeeZCjBN4V4dZJwr5IzNWJfaA45m5n4pgsWVub76NaJcWe9HT0nqId5U",
    "5XJrORLM2XmRCrWrcwqXekfLTzvx/OSUwGfUdls5rbmaYE/qCRe6nBV9QU5W1Qns",
    "Y2ft0MZRP5oNX23qH5u3Jg/qsY3x1cTTKiXRqkVNnX+ohEuZy/0hpdBHGyGGSo/K",
    "LBClpgd1zvs8C/fv1+xZ9ClmtPhSZUAq+NwirT0NSBXY0uUHPXusRvDnNoEiK9+h",
    "UO8MOBZ0wtI/ST3TEA==",
]

def _reconstruct():
    """Concatenate all chunks in order."""
    return "".join(_CHUNKS).encode("ascii")

def _decode(payload):
    """Base64-decode then zlib-inflate the payload."""
    raw = base64.b64decode(payload)
    return zlib.decompress(raw).decode(_ENCODING)

def main():
    payload = _reconstruct()
    text = _decode(payload)
    print(text)

if __name__ == "__main__":
    main()
