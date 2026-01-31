import time
import random
from datetime import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# --- CONFIGURACIÓN ---
URLS_A_RASTREAR = [
    "https://www.amazon.es/dp/B0DN6ZQ3PD", 
    "https://www.amazon.es/dp/B0BCQS37R7"
    "https://www.amazon.es/dp/B0DC8RVRBZ"
]

ARCHIVO_CSV = "historial_precios.csv"

def obtener_driver():
    options = Options()
    # ESTO ES VITAL: --headless hace que funcione sin monitor
    options.add_argument("--headless") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=options)
    return driver

def limpiar_precio(texto_precio):
    try:
        texto = texto_precio.replace("€", "").replace(" ", "").strip()
        texto = texto.replace(".", "").replace(",", ".")
        return float(texto)
    except:
        return None

def rastrear_amazon():
    driver = obtener_driver()
    datos_hoy = []
    
    for url in URLS_A_RASTREAR:
        try:
            print(f"🔍 Visitando: {url}")
            driver.get(url)
            time.sleep(random.uniform(2, 5))
            
            precio_encontrado = None
            titulo = "Producto desconocido"
            
            try:
                titulo = driver.find_element(By.ID, "productTitle").text.strip()
            except:
                pass

            # Estrategia combinada simple
            try:
                entero = driver.find_element(By.CSS_SELECTOR, 'span.a-price-whole').text
                fraccion = driver.find_element(By.CSS_SELECTOR, 'span.a-price-fraction').text
                precio_encontrado = limpiar_precio(f"{entero},{fraccion}")
            except:
                try:
                    # Intento alternativo
                    bloque = driver.find_element(By.CLASS_NAME, "a-price-whole")
                    precio_encontrado = limpiar_precio(bloque.text)
                except:
                    pass

            print(f"   ✅ {titulo[:20]}... -> {precio_encontrado}")
            
            datos_hoy.append({
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "asin": url.split("/dp/")[1].split("/")[0] if "/dp/" in url else "Link",
                "titulo": titulo,
                "precio": precio_encontrado if precio_encontrado else 0,
                "url": url
            })

        except Exception as e:
            print(f"   ❌ Error: {e}")

    driver.quit()
    return datos_hoy

def guardar_datos(nuevos_datos):
    # Guardamos siempre, si existe añade, si no crea
    try:
        df_antiguo = pd.read_csv(ARCHIVO_CSV)
        df_final = pd.concat([df_antiguo, pd.DataFrame(nuevos_datos)], ignore_index=True)
    except FileNotFoundError:
        df_final = pd.DataFrame(nuevos_datos)
        
    df_final.to_csv(ARCHIVO_CSV, index=False)
    print("💾 Guardado en CSV")

if __name__ == "__main__":
    datos = rastrear_amazon()
    guardar_datos(datos)
