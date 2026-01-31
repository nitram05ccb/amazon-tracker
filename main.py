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
    "https://www.amazon.es/dp/B0BCQS37R7",
    "https://www.amazon.es/dp/B0DC8RVRBZ"
]

ARCHIVO_CSV = "historial_precios.csv"

def obtener_driver():
    options = Options()
    # TRUCO MAESTRO: Usamos el modo headless "nuevo" que es más indetectable
    options.add_argument("--headless=new") 
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Headers extendidos para parecer un humano real navegando en Español
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
    options.add_argument("accept-language=es-ES,es;q=0.9")
    
    driver = webdriver.Chrome(options=options)
    return driver

def limpiar_precio(texto_precio):
    try:
        # Limpieza agresiva: quitamos € y espacios
        texto = texto_precio.replace("€", "").replace(" ", "").strip()
        # Formato europeo: quitamos punto de miles, cambiamos coma por punto
        texto = texto.replace(".", "").replace(",", ".")
        val = float(texto)
        return val
    except:
        return None

def rastrear_amazon():
    driver = obtener_driver()
    datos_hoy = []
    
    # Variable para saber si tenemos que guardar una foto de error
    error_detectado = False 

    for url in URLS_A_RASTREAR:
        try:
            print(f"🔍 Visitando: {url}")
            driver.get(url)
            
            # Pausa humana
            time.sleep(random.uniform(3, 6))
            
            precio_encontrado = None
            titulo = "Producto desconocido"
            
            # 1. Intentar sacar el título
            try:
                titulo = driver.find_element(By.ID, "productTitle").text.strip()
            except:
                print("   ⚠️ No encuentro el título (¿Captcha?)")

            # 2. Estrategias de Precio
            # A. Precio grande (whole + fraction)
            if not precio_encontrado:
                try:
                    entero = driver.find_element(By.CSS_SELECTOR, 'span.a-price-whole').text
                    fraccion = driver.find_element(By.CSS_SELECTOR, 'span.a-price-fraction').text
                    precio_encontrado = limpiar_precio(f"{entero},{fraccion}")
                except:
                    pass
            
            # B. Precio "Apex" (ofertas flash)
            if not precio_encontrado:
                try:
                    precio_bloque = driver.find_element(By.CSS_SELECTOR, "span.a-offscreen").get_attribute("textContent")
                    precio_encontrado = limpiar_precio(precio_bloque)
                except:
                    pass

            # DIAGNÓSTICO: Si fallamos, sacamos foto
            if not precio_encontrado or precio_encontrado == 0:
                print("   📸 Fallo al leer precio. Sacando foto de diagnóstico...")
                # Guardamos la foto con el nombre del ASIN para saber cuál falló
                asin = url.split("/dp/")[1].split("/")[0] if "/dp/" in url else "error"
                driver.save_screenshot(f"error_{asin}.png")
                error_detectado = True

            print(f"   ✅ {titulo[:20]}... -> {precio_encontrado}")
            
            datos_hoy.append({
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "asin": url.split("/dp/")[1].split("/")[0] if "/dp/" in url else "Link",
                "titulo": titulo,
                "precio": precio_encontrado if precio_encontrado else 0,
                "url": url
            })

        except Exception as e:
            print(f"   ❌ Error crítico en {url}: {e}")

    driver.quit()
    return datos_hoy

def guardar_datos(nuevos_datos):
    try:
        df_antiguo = pd.read_csv(ARCHIVO_CSV)
        df_final = pd.concat([df_antiguo, pd.DataFrame(nuevos_datos)], ignore_index=True)
    except FileNotFoundError:
        df_final = pd.DataFrame(nuevos_datos)
        
    df_final.to_csv(ARCHIVO_CSV, index=False)
    print("💾 Guardado en CSV")

if __name__ == "__main__":
    rastrear_amazon()
    # Nota: Quitamos el guardar datos del 'if' para asegurar que se guarde siempre dentro de la función, 
    # pero arriba he llamado a rastrear sin guardar. Corrijo:
    datos = rastrear_amazon()
    guardar_datos(datos)
