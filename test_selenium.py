#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mercado Libre Inmuebles - Stage 1
Extracción del inventario base de listings.

Created on Sun Sep 20 2026

@author: edgar.quintero
"""

# ============================================================
# LIBRERÍAS
# ============================================================

import re
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_URL = (
    "https://inmuebles.mercadolibre.com.mx/"
    "venta/jalisco/_NoIndex_True"
)

CHECKPOINT_FILE = "listings_base_checkpoint.csv"
FINAL_FILE = "listings_base.csv"


# ============================================================
# INICIAR SELENIUM
# ============================================================

driver = webdriver.Chrome()

wait = WebDriverWait(
    driver,
    20
)

driver.get(BASE_URL)

driver.maximize_window()


# ============================================================
# CERRAR AVISOS INICIALES
# ============================================================

# Primer aviso

wait.until(
    EC.element_to_be_clickable(
        (
            By.XPATH,
            "//button[@data-testid='action:understood-button']"
        )
    )
).click()


# Segundo aviso

wait.until(
    EC.element_to_be_clickable(
        (
            By.XPATH,
            "//span[@data-andes-button-content='true' "
            "and normalize-space()='Entendido']"
        )
    )
).click()


# ============================================================
# FUNCIÓN PARA EXTRAER LISTINGS DE LA PÁGINA ACTUAL
# ============================================================

def extraer_listings_pagina(driver):

    # Esperar a que aparezca por lo menos un listing
    wait.until(
        EC.presence_of_element_located(
            (
                By.CSS_SELECTOR,
                "a.poly-component__title"
            )
        )
    )

    # Encontrar todos los listings
    cards = driver.find_elements(
        By.CSS_SELECTOR,
        "a.poly-component__title"
    )

    listings = []

    for card in cards:

        # ----------------------------------------------------
        # TÍTULO
        # ----------------------------------------------------

        title = card.text.strip()


        # ----------------------------------------------------
        # URL
        # ----------------------------------------------------

        url = card.get_attribute("href")

        # Quitamos parámetros de tracking después del #
        if url:
            url = url.split("#")[0]


        # ----------------------------------------------------
        # LISTING ID
        # ----------------------------------------------------

        match = re.search(
            r"MLM-(\d+)",
            url
        )

        listing_id = (
            match.group(1)
            if match
            else None
        )


        # ----------------------------------------------------
        # PROPERTY TYPE
        # ----------------------------------------------------

        if "departamento.mercadolibre" in url:

            property_type = "Departamento"

        elif "casa.mercadolibre" in url:

            property_type = "Casa"

        else:

            property_type = None


        # ----------------------------------------------------
        # GUARDAR LISTING
        # ----------------------------------------------------

        listings.append(
            {
                "listing_id": listing_id,
                "title": title,
                "property_type": property_type,
                "url": url
            }
        )


    return listings


# ============================================================
# EXTRAER TODAS LAS PÁGINAS
# ============================================================

listings = []

numero_pagina = 1


try:

    while True:

        print("\n")
        print("=" * 50)
        print(
            f"EXTRAYENDO PÁGINA {numero_pagina}"
        )
        print("=" * 50)


        # ----------------------------------------------------
        # EXTRAER PÁGINA ACTUAL
        # ----------------------------------------------------

        listings_pagina = (
            extraer_listings_pagina(driver)
        )

        print(
            "Listings encontrados:",
            len(listings_pagina)
        )


        # ----------------------------------------------------
        # AGREGAR AL DATASET GENERAL
        # ----------------------------------------------------

        listings.extend(
            listings_pagina
        )

        print(
            "Total acumulado:",
            len(listings)
        )


        # ----------------------------------------------------
        # INFORMACIÓN DE IDs
        # ----------------------------------------------------

        df_checkpoint = pd.DataFrame(
            listings
        )

        ids_unicos = (
            df_checkpoint["listing_id"]
            .nunique()
        )

        duplicados = (
            df_checkpoint["listing_id"]
            .duplicated()
            .sum()
        )

        print(
            "IDs únicos:",
            ids_unicos
        )

        print(
            "Duplicados acumulados:",
            duplicados
        )


        # ----------------------------------------------------
        # GUARDAR CHECKPOINT
        # ----------------------------------------------------

        df_checkpoint.to_csv(
            CHECKPOINT_FILE,
            index=False,
            encoding="utf-8-sig"
        )

        print(
            "Checkpoint guardado."
        )


        # ----------------------------------------------------
        # BUSCAR BOTÓN SIGUIENTE
        # ----------------------------------------------------

        botones_siguiente = (
            driver.find_elements(
                By.XPATH,
                "//span["
                "@class='andes-pagination__arrow-title' "
                "and normalize-space()='Siguiente'"
                "]"
            )
        )


        # ----------------------------------------------------
        # SI NO EXISTE, TERMINAMOS
        # ----------------------------------------------------

        if len(botones_siguiente) == 0:

            print("\n")
            print(
                "🏁 Ya no existe el botón Siguiente."
            )

            print(
                "Última página alcanzada."
            )

            break


        # ----------------------------------------------------
        # GUARDAR UN ELEMENTO DE LA PÁGINA ACTUAL
        # ----------------------------------------------------

        primer_listing = (
            driver.find_element(
                By.CSS_SELECTOR,
                "a.poly-component__title"
            )
        )


        # ----------------------------------------------------
        # CLICK EN SIGUIENTE
        # ----------------------------------------------------

        botones_siguiente[0].click()


        # ----------------------------------------------------
        # ESPERAR QUE DESAPAREZCA LA PÁGINA ANTERIOR
        # ----------------------------------------------------

        wait.until(
            EC.staleness_of(
                primer_listing
            )
        )


        # ----------------------------------------------------
        # ESPERAR NUEVOS LISTINGS
        # ----------------------------------------------------

        wait.until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "a.poly-component__title"
                )
            )
        )


        # ----------------------------------------------------
        # SIGUIENTE ITERACIÓN
        # ----------------------------------------------------

        numero_pagina += 1


# ============================================================
# SI ALGO FALLA
# ============================================================

except Exception as e:

    print("\n")
    print("=" * 50)
    print("⚠️ EL SCRIPT SE DETUVO")
    print("=" * 50)

    print(
        "Página donde ocurrió:",
        numero_pagina
    )

    print(
        "Error:",
        e
    )

    print(
        "\nNo pasa nada:"
        "\nel checkpoint conserva lo extraído."
    )


# ============================================================
# SIEMPRE EJECUTAR AL FINAL
# ============================================================

finally:

    # --------------------------------------------------------
    # CREAR DATAFRAME
    # --------------------------------------------------------

    df_listings = pd.DataFrame(
        listings
    )


    # --------------------------------------------------------
    # VALIDACIONES
    # --------------------------------------------------------

    print("\n")
    print("=" * 50)
    print("RESULTADOS")
    print("=" * 50)

    print(
        "Páginas procesadas:",
        numero_pagina
    )

    print(
        "Registros extraídos:",
        len(df_listings)
    )


    if len(df_listings) > 0:

        print(
            "IDs únicos:",
            df_listings[
                "listing_id"
            ].nunique()
        )

        print(
            "Duplicados:",
            df_listings[
                "listing_id"
            ].duplicated().sum()
        )

        print(
            "IDs nulos:",
            df_listings[
                "listing_id"
            ].isna().sum()
        )


        # ----------------------------------------------------
        # QUITAR DUPLICADOS
        # ----------------------------------------------------

        df_listings = (
            df_listings
            .drop_duplicates(
                subset="listing_id"
            )
            .reset_index(
                drop=True
            )
        )


        print(
            "\nRegistros finales "
            "después de quitar duplicados:",
            len(df_listings)
        )


        # ----------------------------------------------------
        # GUARDAR DATASET FINAL
        # ----------------------------------------------------

        df_listings.to_csv(
            FINAL_FILE,
            index=False,
            encoding="utf-8-sig"
        )

        print(
            "\nDataset final guardado:"
        )

        print(
            FINAL_FILE
        )


    # --------------------------------------------------------
    # CERRAR CHROME
    # --------------------------------------------------------

    driver.quit()

    print(
        "\nChrome cerrado."
    )
