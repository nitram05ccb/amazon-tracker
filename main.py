import time
import random
from datetime import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium_stealth import stealth

# --- CONFIGURACIÓN ---
URLS_A_RASTREAR = [
    "https://www.amazon.es/dp/B0DN6ZQ3PD", 
    "https://www.amazon.es/dp/B0BCQS37R7",
    "https://www.amazon.es/dp/B0DC8RVRBZ"
]

ARCHIVO_CSV = "historial_precios.csv"

def obtener_driver():
    options = Options()
    options.add_argument("--headless=new") 
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=options)

    stealth(driver,
        languages=["es-ES", "es"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )
    return driver

def limpiar_precio(texto_precio):
    try:
        texto = texto_precio.replace("€", "").replace(" ", "").strip()
        texto = texto.replace(".", "").replace(",", ".") 
        return float(texto)
    except:
        return None

def intentar_pasar_bloqueo(driver):
    try:
        posibles_botones = driver.find_elements(By.XPATH, "//*[contains(text(), 'Seguir comprando')]")
        if len(posibles_botones) > 0:
            posibles_botones[0].click()
            time.sleep(2)
            return True
        
        # Aceptar cookies para limpiar la pantalla
        cookies = driver.find_elements(By.ID, "sp-cc-accept")
        if len(cookies) > 0:
            cookies[0].click()
            time.sleep(1)
    except:
        pass

def rastrear_amazon():
    driver = obtener_driver()
    datos_hoy = []
    
    for url in URLS_A_RASTREAR:
        try:
            print(f"🔍 Visitando: {url}")
            driver.get(url)
            time.sleep(random.uniform(2, 5))
            intentar_pasar_bloqueo(driver)
            
            precio_encontrado = None
            titulo = "Producto desconocido"
            asin = url.split("/dp/")[1].split("/")[0] if "/dp/" in url else "Link"
            
            try:
                titulo = driver.find_element(By.ID, "productTitle").text.strip()
            except:
                pass

            # Búsqueda de precio
            if not precio_encontrado:
                try:
                    entero = driver.find_element(By.CSS_SELECTOR, 'span.a-price-whole').text
                    fraccion = driver.find_element(By.CSS_SELECTOR, 'span.a-price-fraction').text
                    precio_encontrado = limpiar_precio(f"{entero},{fraccion}")
                except:
                    pass
            
            if not precio_encontrado:
                try:
                    bloque = driver.find_element(By.CSS_SELECTOR, "span.a-offscreen").get_attribute("textContent")
                    precio_encontrado = limpiar_precio(bloque)
                except:
                    pass

            # --- NUEVO: FOTO OBLIGATORIA (EVIDENCIA) ---
            # Guardamos la foto SIEMPRE para ver qué está viendo el robot
            print(f"   📸 Guardando evidencia de {asin}...")
            driver.save_screenshot(f"evidencia_{asin}.png")

            print(f"   ✅ {titulo[:20]}... -> {precio_encontrado}")
            
            datos_hoy.append({
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "asin": asin,
                "titulo": titulo,
                "precio": precio_encontrado if precio_encontrado else 0,
                "url": url
            })

        except Exception as e:
            print(f"   ❌ Error: {e}")

    driver.quit()
    return datos_hoy

def guardar_datos(nuevos_datos):
    try:
        df_antiguo = pd.read_csv(ARCHIVO_CSV)
        df_final = pd.concat([df_antiguo, pd.DataFrame(nuevos_datos)], ignore_index=True)
    except FileNotFoundError:
        df_final = pd.DataFrame(nuevos_datos)
        
    df_final.to_csv(ARCHIVO_CSV, index=False)

if __name__ == "__main__":
    datos = rastrear_amazon()
    guardar_datos(datos)
