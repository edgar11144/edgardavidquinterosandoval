#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 21 20:34:53 2026

@author: edgar.quintero

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

Mercado Libre Inmuebles - Stage 2 POC v2

INPUT:
    listings_base.csv

OUTPUTS:
    stage2_properties_test.csv
    stage2_property_features_test.csv
    stage2_development_units_test.csv
    stage2_poi_test.csv

OBJETIVO:
    Enriquecer detail pages de Mercado Libre.

ESTRUCTURA:
    - properties:
        una fila por listing

    - property_features:
        una fila por característica encontrada

    - development_units:
        una fila por unidad/prototipo de un desarrollo

    - poi:
        una fila por punto de interés

NOTA:
    TEST_MODE = True procesa una muestra aleatoria.
    NO cambiar a False hasta validar el POC.
"""


# ============================================================
# LIBRERÍAS
# ============================================================

import re
import json
import time
from datetime import datetime

import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
    ElementNotInteractableException
)


# ============================================================
# CONFIGURACIÓN
# ============================================================

INPUT_FILE = "listings_base.csv"

OUTPUT_DIR = Path.home() / "TOG_stage2_local"
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_PROPERTIES = OUTPUT_DIR / "stage2_properties.csv"
OUTPUT_FEATURES = OUTPUT_DIR / "stage2_property_features.csv"
OUTPUT_UNITS = OUTPUT_DIR / "stage2_development_units.csv"
OUTPUT_POI = OUTPUT_DIR / "stage2_poi.csv"

TEST_MODE = False
RESUME = True

CHECKPOINT_EVERY = 25

# ------------------------------------------------------------
# POC
# ------------------------------------------------------------

TEST_MODE = False
SAMPLE_SIZE = 50
RANDOM_STATE = 42


# ------------------------------------------------------------
# REANUDACIÓN
# ------------------------------------------------------------

RESUME = True


# ------------------------------------------------------------
# SELENIUM
# ------------------------------------------------------------

TIMEOUT = 5

# Pausa fija para no martillar el sitio.
# No tiene propósito de evasión.
SLEEP_BETWEEN_LISTINGS = 1.0


# ============================================================
# UTILIDADES GENERALES
# ============================================================

def safe_text(elements):

    if not elements:
        return None

    try:

        value = elements[0].text.strip()

        return value if value else None

    except Exception:
        return None


def normalize_listing_id(value):

    if pd.isna(value):
        return None

    value = str(value).strip()

    # En caso de que pandas haya convertido accidentalmente
    # algo a "123456.0"
    if value.endswith(".0"):
        value = value[:-2]

    return value


def unique_preserve_order(values):

    output = []
    seen = set()

    for value in values:

        if value not in seen:

            output.append(value)
            seen.add(value)

    return output


# ============================================================
# PARSERS NUMÉRICOS
# ============================================================

def parse_numbers(text):

    """
    Ejemplos:

    "207 m²"
        -> [207]

    "70 m² a 99 m²"
        -> [70, 99]

    "1,000 m²"
        -> [1000]

    "1 a 2"
        -> [1, 2]
    """

    if text is None:
        return []


    matches = re.findall(
        r"\d[\d,]*(?:\.\d+)?",
        str(text)
    )


    values = []


    for match in matches:

        try:

            value = float(
                match.replace(",", "")
            )

            values.append(value)

        except ValueError:
            continue


    return values


def parse_range(text):

    numbers = parse_numbers(
        text
    )

    if not numbers:
        return None, None


    if len(numbers) == 1:
        return numbers[0], numbers[0]


    return numbers[0], numbers[-1]


def parse_single_number(text):

    numbers = parse_numbers(
        text
    )

    if not numbers:
        return None

    return numbers[0]


def parse_price_text(text):

    if text is None:
        return None

    numbers = parse_numbers(
        text
    )

    if not numbers:
        return None

    return numbers[0]


# ============================================================
# CARGAR CSV EXISTENTE
# ============================================================

def load_existing(path):

    try:

        df = pd.read_csv(
            path,
            dtype={
                "listing_id": str
            }
        )

        if "listing_id" in df.columns:

            df["listing_id"] = (
                df["listing_id"]
                .apply(normalize_listing_id)
            )

        return df.to_dict(
            "records"
        )

    except FileNotFoundError:
        return []

    except pd.errors.EmptyDataError:
        return []


# ============================================================
# ELIMINAR VERSIONES PREVIAS DE UN LISTING
# ============================================================

def remove_listing(rows, listing_id):

    return [
        row
        for row in rows
        if normalize_listing_id(
            row.get("listing_id")
        ) != listing_id
    ]


# ============================================================
# GUARDAR OUTPUTS
# ============================================================

def save_rows(rows, path):

    if not rows:
        return

    df = pd.DataFrame(
        rows
    )

    df.to_csv(
        path,
        index=False,
        encoding="utf-8-sig"
    )


def save_all(
    properties,
    features,
    units,
    pois
):

    save_rows(
        properties,
        OUTPUT_PROPERTIES
    )

    save_rows(
        features,
        OUTPUT_FEATURES
    )

    save_rows(
        units,
        OUTPUT_UNITS
    )

    save_rows(
        pois,
        OUTPUT_POI
    )


# ============================================================
# POPUPS
# ============================================================

def close_popups(driver):

    selectors = [

        (
            By.XPATH,
            "//button[@data-testid="
            "'action:understood-button']"
        ),

        (
            By.XPATH,
            "//span["
            "@data-andes-button-content='true' "
            "and normalize-space()='Entendido'"
            "]"
        )
    ]


    for selector in selectors:

        try:

            button = WebDriverWait(
                driver,
                2
            ).until(
                EC.element_to_be_clickable(
                    selector
                )
            )

            button.click()

        except Exception:
            pass


# ============================================================
# ESPERAR DETAIL PAGE
# ============================================================

def wait_detail_page(
    driver,
    wait
):

    wait.until(
        EC.presence_of_element_located(
            (
                By.CSS_SELECTOR,
                "h1.ui-pdp-title"
            )
        )
    )


# ============================================================
# SCROLL PARA CARGAR SECCIONES LAZY
# ============================================================

def load_lazy_sections(driver):

    try:

        height = driver.execute_script(
            "return document.body.scrollHeight;"
        )


        positions = [
            0.20,
            0.40,
            0.60,
            0.80,
            1.00
        ]


        for fraction in positions:

            driver.execute_script(
                "window.scrollTo(0, arguments[0]);",
                int(height * fraction)
            )

            time.sleep(
                0.25
            )


    except Exception:
        pass


# ============================================================
# TÍTULO / SUBTÍTULO
# ============================================================

def extract_title(driver):

    return safe_text(
        driver.find_elements(
            By.CSS_SELECTOR,
            "h1.ui-pdp-title"
        )
    )


def extract_subtitle(driver):

    return safe_text(
        driver.find_elements(
            By.CSS_SELECTOR,
            ".ui-pdp-subtitle"
        )
    )


# ============================================================
# INDIVIDUAL VS DEVELOPMENT
# ============================================================

def detect_listing_type(driver):

    units = driver.find_elements(
        By.CSS_SELECTOR,
        ".ui-vip-available-units__unit-container"
    )


    if units:
        return "development"


    subtitle = extract_subtitle(
        driver
    )


    if (
        subtitle
        and
        "desarrollo" in subtitle.lower()
    ):
        return "development"


    return "individual"


# ============================================================
# PRECIO
# ============================================================

def extract_price(driver):

    # Fuente preferida:
    # meta estructurado

    elements = driver.find_elements(
        By.CSS_SELECTOR,
        '#price meta[itemprop="price"]'
    )


    if elements:

        value = elements[0].get_attribute(
            "content"
        )

        try:

            return float(value)

        except (
            TypeError,
            ValueError
        ):
            pass


    # Fallback visual

    elements = driver.find_elements(
        By.CSS_SELECTOR,
        "#price .andes-money-amount__fraction"
    )


    text = safe_text(
        elements
    )


    return parse_price_text(
        text
    )


# ============================================================
# MONEDA
# ============================================================

def extract_currency(driver):

    elements = driver.find_elements(
        By.CSS_SELECTOR,
        '#price [itemprop="priceCurrency"]'
    )


    if not elements:
        return None


    try:

        text = elements[0].text.strip()

        if text:
            return text

    except Exception:
        pass


    try:

        return elements[0].get_attribute(
            "content"
        )

    except Exception:
        return None


# ============================================================
# UBICACIÓN
# ============================================================

def extract_address(driver):

    # --------------------------------------------------------
    # Método preferido:
    # usar "Ver información de la zona"
    # --------------------------------------------------------

    links = driver.find_elements(
        By.CSS_SELECTOR,
        ".ui-vip-location__poi-link"
    )


    if links:

        try:

            parent = links[0].find_element(
                By.XPATH,
                "./parent::*"
            )


            location = parent.find_elements(
                By.CSS_SELECTOR,
                ".ui-pdp-media__title"
            )


            text = safe_text(
                location
            )


            if text:
                return text


        except Exception:
            pass


    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

    candidates = driver.find_elements(
        By.CSS_SELECTOR,
        ".ui-pdp-media__title"
    )


    geography_words = [

        "Jalisco",
        "Zapopan",
        "Guadalajara",
        "Tlaquepaque",
        "Tlajomulco",
        "Tonalá"
    ]


    for candidate in candidates:

        try:

            text = candidate.text.strip()

            if any(
                word.lower()
                in text.lower()
                for word
                in geography_words
            ):

                return text

        except Exception:
            continue


    return None


# ============================================================
# DESCRIPCIÓN
# ============================================================

def extract_description(driver):

    selectors = [

        "#description .ui-pdp-description__content",

        ".ui-pdp-description__content"
    ]


    for selector in selectors:

        elements = driver.find_elements(
            By.CSS_SELECTOR,
            selector
        )


        text = safe_text(
            elements
        )


        if text:
            return text


    return None


# ============================================================
# SELLER
# ============================================================

def extract_seller(driver):

    seller_name = None
    seller_id = None
    seller_verified = False


    # --------------------------------------------------------
    # NOMBRE
    # --------------------------------------------------------

    names = driver.find_elements(
        By.CSS_SELECTOR,
        "#seller_profile "
        ".ui-vip-profile-info__info-container h3"
    )


    seller_name = safe_text(
        names
    )


    # --------------------------------------------------------
    # SELLER ID
    # --------------------------------------------------------

    links = driver.find_elements(
        By.CSS_SELECTOR,
        "#seller_profile a[href*='_CustId_']"
    )


    if links:

        try:

            href = links[0].get_attribute(
                "href"
            )


            match = re.search(
                r"_CustId_(\d+)",
                href or ""
            )


            if match:

                seller_id = match.group(1)

        except Exception:
            pass


    # --------------------------------------------------------
    # VERIFIED
    # --------------------------------------------------------

    verified = driver.find_elements(
        By.CSS_SELECTOR,
        "#seller_profile "
        ".ui-vip-profile-info__icon-normal"
    )


    seller_verified = (
        len(verified) > 0
    )


    return {

        "seller_name":
            seller_name,

        "seller_id":
            seller_id,

        "seller_verified":
            seller_verified
    }


# ============================================================
# EXPANDIR CARACTERÍSTICAS
# ============================================================

def expand_individual_specs(driver):

    """
    Sólo intenta expandir el componente inline.

    No seguimos links /specifications.
    """

    buttons = driver.find_elements(
        By.CSS_SELECTOR,
        "#highlighted_specs_attrs "
        "[data-testid='action-collapsable-target']"
    )


    if not buttons:

        return False


    button = buttons[0]


    try:

        text = button.text.strip().lower()


        # Ya está expandido.
        if "ocultar" in text:

            return True


        if "ver todas" not in text:

            return False


        driver.execute_script(
            """
            arguments[0].scrollIntoView({
                block: 'center'
            });
            """,
            button
        )


        try:

            button.click()

        except (
            ElementClickInterceptedException,
            ElementNotInteractableException
        ):

            driver.execute_script(
                "arguments[0].click();",
                button
            )


        WebDriverWait(
            driver,
            5
        ).until(
            lambda d:
            len(
                d.find_elements(
                    By.CSS_SELECTOR,
                    "#highlighted_specs_attrs "
                    "table.andes-table tbody tr"
                )
            ) > 0
        )


        return True


    except Exception:
        return False


# ============================================================
# FEATURES INDIVIDUALES
# ============================================================

def extract_individual_features(
    driver,
    listing_id
):

    output = []


    sections = driver.find_elements(
        By.CSS_SELECTOR,
        "#highlighted_specs_attrs"
    )


    if not sections:

        return output


    section = sections[0]


    # ========================================================
    # 1. FEATURES DESTACADAS
    # ========================================================

    highlighted = {}


    items = section.find_elements(
        By.CSS_SELECTOR,
        ".ui-vpp-highlighted-specs__"
        "key-value__labels__key-value"
    )


    for item in items:

        try:

            text = item.text.strip()


            if ":" not in text:
                continue


            name, value = text.split(
                ":",
                1
            )


            name = name.strip()
            value = value.strip()


            if name and value:

                highlighted[
                    name
                ] = value

        except Exception:
            continue


    # ========================================================
    # 2. FEATURES COMPLETAS EN TABLAS
    # ========================================================

    full_features = []

    full_feature_names = set()


    blocks = section.find_elements(
        By.CSS_SELECTOR,
        ".ui-vpp-striped-specs"
    )


    for block in blocks:

        # Puede haber más de una tabla dentro del bloque.

        tables = block.find_elements(
            By.CSS_SELECTOR,
            ".ui-vpp-striped-specs__table"
        )


        for table in tables:

            # ------------------------------------------------
            # CATEGORÍA
            # ------------------------------------------------

            headers = table.find_elements(
                By.CSS_SELECTOR,
                ".ui-vpp-striped-specs__header"
            )


            category = safe_text(
                headers
            )


            if not category:

                category = (
                    "Características del inmueble"
                )


            # ------------------------------------------------
            # FILAS
            # ------------------------------------------------

            rows = table.find_elements(
                By.CSS_SELECTOR,
                "table.andes-table tbody tr"
            )


            for row in rows:

                try:

                    name = row.find_element(
                        By.CSS_SELECTOR,
                        "th"
                    ).text.strip()


                    value = row.find_element(
                        By.CSS_SELECTOR,
                        "td"
                    ).text.strip()


                    if not name or not value:
                        continue


                    full_feature_names.add(
                        name
                    )


                    full_features.append(
                        {
                            "listing_id":
                                listing_id,

                            "category":
                                category,

                            "feature":
                                name,

                            "value":
                                value
                        }
                    )


                except Exception:
                    continue


    # ========================================================
    # 3. DESTACADAS QUE NO ESTÁN REPETIDAS EN LA TABLA
    # ========================================================

    for name, value in highlighted.items():

        if name in full_feature_names:
            continue


        output.append(
            {
                "listing_id":
                    listing_id,

                "category":
                    "Destacadas",

                "feature":
                    name,

                "value":
                    value
            }
        )


    # ========================================================
    # 4. FEATURES COMPLETAS
    # ========================================================

    output.extend(
        full_features
    )


    return output


# ============================================================
# FEATURES DE DESARROLLO
# ============================================================

def extract_development_features(
    driver,
    listing_id
):

    output = []


    # Los desarrollos usan con frecuencia
    # una tabla Andes simple.

    tables = driver.find_elements(
        By.CSS_SELECTOR,
        "table.andes-table"
    )


    for table in tables:

        rows = table.find_elements(
            By.CSS_SELECTOR,
            "tbody tr"
        )


        for row in rows:

            try:

                name = row.find_element(
                    By.CSS_SELECTOR,
                    "th"
                ).text.strip()


                value = row.find_element(
                    By.CSS_SELECTOR,
                    "td"
                ).text.strip()


                if not name or not value:
                    continue


                output.append(
                    {
                        "listing_id":
                            listing_id,

                        "category":
                            "Características del inmueble",

                        "feature":
                            name,

                        "value":
                            value
                    }
                )


            except Exception:
                continue


    # Deduplicar
    seen = set()
    deduped = []


    for row in output:

        key = (
            row["feature"],
            row["value"]
        )


        if key in seen:
            continue


        seen.add(
            key
        )

        deduped.append(
            row
        )


    return deduped


# ============================================================
# EXTRAER LISTA ACTIVA DE UN TAB
# ============================================================

def extract_development_tab(
    driver,
    tab_name
):

    """
    Se usa para:
        Ambientes
        Comodidades y equipamiento

    Si no puede identificar/clickear el tab,
    devuelve [].
    """

    candidates = driver.find_elements(
        By.XPATH,
        f"//*[normalize-space()='{tab_name}']"
    )


    candidate = None


    for element in candidates:

        try:

            if element.is_displayed():

                candidate = element
                break

        except Exception:
            continue


    if candidate is None:
        return []


    try:

        driver.execute_script(
            """
            arguments[0].scrollIntoView({
                block: 'center'
            });
            """,
            candidate
        )


        try:

            candidate.click()

        except Exception:

            driver.execute_script(
                "arguments[0].click();",
                candidate
            )


        time.sleep(
            0.4
        )


    except Exception:
        return []


    values = []


    containers = driver.find_elements(
        By.CSS_SELECTOR,
        ".ui-pdp-list.ui-pdp-specs__list"
    )


    for container in containers:

        try:

            if not container.is_displayed():
                continue

        except Exception:
            continue


        items = container.find_elements(
            By.CSS_SELECTOR,
            "li.ui-pdp-list__item"
        )


        for item in items:

            try:

                text = item.text.strip()

                if text:
                    values.append(
                        text
                    )

            except Exception:
                continue


    return unique_preserve_order(
        values
    )


# ============================================================
# HIGHLIGHTED SPECS RES
# ============================================================

def extract_highlighted_specs(driver):

    output = []


    elements = driver.find_elements(
        By.CSS_SELECTOR,
        "#highlighted_specs_res "
        ".ui-pdp-highlighted-specs-res__icon-label"
    )


    for element in elements:

        try:

            text = element.text.strip()

            if text:
                output.append(
                    text
                )

        except Exception:
            continue


    return output


# ============================================================
# CONVERTIR FEATURES A DICT
# ============================================================

def features_to_dict(features):

    output = {}


    for row in features:

        name = row.get(
            "feature"
        )

        value = row.get(
            "value"
        )


        if name and value:

            output[name] = value


    return output


# ============================================================
# VARIABLES ESTRUCTURALES
# ============================================================

def extract_structural_fields(
    feature_dict,
    highlighted_specs
):

    total_min = None
    total_max = None

    constructed_min = None
    constructed_max = None

    bedrooms_min = None
    bedrooms_max = None

    bathrooms_min = None
    bathrooms_max = None

    parking_min = None
    parking_max = None

    age_years = None


    # --------------------------------------------------------
    # FEATURES PRINCIPALES
    # --------------------------------------------------------

    for key, value in feature_dict.items():

        normalized = (
            key.strip()
            .lower()
        )


        if normalized == "superficie total":

            (
                total_min,
                total_max
            ) = parse_range(
                value
            )


        elif normalized == "superficie construida":

            (
                constructed_min,
                constructed_max
            ) = parse_range(
                value
            )


        elif normalized in (
            "recámaras",
            "recamaras"
        ):

            (
                bedrooms_min,
                bedrooms_max
            ) = parse_range(
                value
            )


        elif normalized in (
            "baños",
            "banos"
        ):

            (
                bathrooms_min,
                bathrooms_max
            ) = parse_range(
                value
            )


        elif normalized == "estacionamientos":

            (
                parking_min,
                parking_max
            ) = parse_range(
                value
            )


        elif normalized == "antigüedad":

            age_years = parse_single_number(
                value
            )


    # --------------------------------------------------------
    # FALLBACK:
    # highlighted_specs_res
    # --------------------------------------------------------

    for text in highlighted_specs:

        lower = text.lower()


        if (
            total_min is None
            and
            "m² total" in lower
        ):

            (
                total_min,
                total_max
            ) = parse_range(
                text
            )


        if (
            bedrooms_min is None
            and
            (
                "rec." in lower
                or
                "recámara" in lower
                or
                "recamara" in lower
            )
        ):

            (
                bedrooms_min,
                bedrooms_max
            ) = parse_range(
                text
            )


        if (
            bathrooms_min is None
            and
            (
                "baño" in lower
                or
                "bano" in lower
            )
        ):

            (
                bathrooms_min,
                bathrooms_max
            ) = parse_range(
                text
            )


    return {

        "total_m2_min":
            total_min,

        "total_m2_max":
            total_max,

        "construction_m2_min":
            constructed_min,

        "construction_m2_max":
            constructed_max,

        "bedrooms_min":
            bedrooms_min,

        "bedrooms_max":
            bedrooms_max,

        "bathrooms_min":
            bathrooms_min,

        "bathrooms_max":
            bathrooms_max,

        "parking_min":
            parking_min,

        "parking_max":
            parking_max,

        "age_years":
            age_years
    }


# ============================================================
# UNIDADES DE DESARROLLO
# ============================================================

def extract_development_units(
    driver,
    listing_id
):

    output = []


    cards = driver.find_elements(
        By.CSS_SELECTOR,
        ".ui-vip-available-units__unit-container"
    )


    for unit_number, card in enumerate(
        cards,
        start=1
    ):

        price_text = None
        details_text = None


        # ----------------------------------------------------
        # PRECIO
        # ----------------------------------------------------

        try:

            price_text = card.find_element(
                By.CSS_SELECTOR,
                ".ui-vip-available-units__unit-info h3"
            ).text.strip()

        except Exception:
            pass


        # ----------------------------------------------------
        # DETALLE
        # ----------------------------------------------------

        try:

            paragraphs = card.find_elements(
                By.CSS_SELECTOR,
                ".ui-vip-available-units__unit-info p"
            )


            if paragraphs:

                details_text = (
                    paragraphs[-1]
                    .text
                    .strip()
                )

        except Exception:
            pass


        price = parse_price_text(
            price_text
        )


        bedrooms = None
        bathrooms = None
        construction_m2 = None


        if details_text:

            match = re.search(
                r"(\d+)\s*rec",
                details_text,
                flags=re.IGNORECASE
            )


            if match:

                bedrooms = int(
                    match.group(1)
                )


            match = re.search(
                r"(\d+)\s*bañ",
                details_text,
                flags=re.IGNORECASE
            )


            if match:

                bathrooms = int(
                    match.group(1)
                )


            match = re.search(
                r"([\d,.]+)\s*m²\s*constru",
                details_text,
                flags=re.IGNORECASE
            )


            if match:

                try:

                    construction_m2 = float(
                        match.group(1)
                        .replace(",", "")
                    )

                except ValueError:
                    pass


        output.append(
            {
                "listing_id":
                    listing_id,

                "unit_number":
                    unit_number,

                "price":
                    price,

                "bedrooms":
                    bedrooms,

                "bathrooms":
                    bathrooms,

                "construction_m2":
                    construction_m2,

                "price_text_raw":
                    price_text,

                "unit_details_raw":
                    details_text,

                "scraped_at":
                    datetime.now()
            }
        )


    return output


# ============================================================
# POINTS OF INTEREST
# ============================================================

def extract_poi(
    driver,
    listing_id
):

    output = []


    containers = driver.find_elements(
        By.CSS_SELECTOR,
        "#points_of_interest"
    )


    if not containers:
        return output


    container = containers[0]


    panels = container.find_elements(
        By.CSS_SELECTOR,
        ".ui-vip-poi__panel"
    )


    for panel in panels:

        category = None


        try:

            category = panel.find_element(
                By.CSS_SELECTOR,
                ".ui-vip-poi__header-title"
            ).text.strip()

        except Exception:
            pass


        subsections = panel.find_elements(
            By.CSS_SELECTOR,
            ".ui-vip-poi__subsection"
        )


        for subsection in subsections:

            subtype = None


            try:

                subtype = subsection.find_element(
                    By.CSS_SELECTOR,
                    ".ui-vip-poi__subsection-title"
                ).text.strip()

            except Exception:
                pass


            items = subsection.find_elements(
                By.CSS_SELECTOR,
                ".ui-vip-poi__item"
            )


            for item in items:

                poi_name = None
                subtitle = None

                walking_min = None
                distance_m = None


                try:

                    poi_name = item.find_element(
                        By.CSS_SELECTOR,
                        "[data-testid='title']"
                    ).text.strip()

                except Exception:
                    pass


                try:

                    subtitle = item.find_element(
                        By.CSS_SELECTOR,
                        "[data-testid='subtitle']"
                    ).text.strip()

                except Exception:
                    pass


                if subtitle:

                    match = re.search(
                        r"(\d+)\s*min",
                        subtitle,
                        flags=re.IGNORECASE
                    )


                    if match:

                        walking_min = int(
                            match.group(1)
                        )


                    match = re.search(
                        r"([\d,]+)\s*metros",
                        subtitle,
                        flags=re.IGNORECASE
                    )


                    if match:

                        distance_m = int(
                            match.group(1)
                            .replace(",", "")
                        )


                output.append(
                    {
                        "listing_id":
                            listing_id,

                        "category":
                            category,

                        "subtype":
                            subtype,

                        "poi_name":
                            poi_name,

                        "walking_min":
                            walking_min,

                        "distance_m":
                            distance_m,

                        "poi_details_raw":
                            subtitle,

                        "scraped_at":
                            datetime.now()
                    }
                )


    return output


# ============================================================
# PROCESAR LISTING
# ============================================================

def process_listing(
    driver,
    wait,
    row
):

    listing_id = normalize_listing_id(
        row["listing_id"]
    )


    url = row[
        "url"
    ]


    # --------------------------------------------------------
    # ABRIR PÁGINA
    # --------------------------------------------------------

    driver.get(
        url
    )


    close_popups(
        driver
    )


    wait_detail_page(
        driver,
        wait
    )


    # --------------------------------------------------------
    # CARGAR SECCIONES LAZY
    # --------------------------------------------------------

    load_lazy_sections(
        driver
    )


    # --------------------------------------------------------
    # DATOS GENERALES
    # --------------------------------------------------------

    title = extract_title(
        driver
    )


    subtitle = extract_subtitle(
        driver
    )


    listing_type = detect_listing_type(
        driver
    )


    price = extract_price(
        driver
    )


    currency = extract_currency(
        driver
    )


    address = extract_address(
        driver
    )


    description = extract_description(
        driver
    )


    seller = extract_seller(
        driver
    )


    # --------------------------------------------------------
    # HIGHLIGHTED SPECS
    # --------------------------------------------------------

    highlighted_specs = extract_highlighted_specs(
        driver
    )


    # ========================================================
    # FEATURES
    # ========================================================

    ambientes = []
    amenities = []


    if listing_type == "individual":

        expand_individual_specs(
            driver
        )


        features = extract_individual_features(
            driver,
            listing_id
        )


    else:

        features = extract_development_features(
            driver,
            listing_id
        )


        # Tabs propios de desarrollos

        ambientes = extract_development_tab(
            driver,
            "Ambientes"
        )


        amenities = extract_development_tab(
            driver,
            "Comodidades y equipamiento"
        )


        # Meterlos también en la tabla larga

        existing = {
            (
                row["category"],
                row["feature"],
                row["value"]
            )
            for row
            in features
        }


        for item in ambientes:

            key = (
                "Ambientes",
                item,
                "Sí"
            )


            if key not in existing:

                features.append(
                    {
                        "listing_id":
                            listing_id,

                        "category":
                            "Ambientes",

                        "feature":
                            item,

                        "value":
                            "Sí"
                    }
                )


        for item in amenities:

            key = (
                "Comodidades y equipamiento",
                item,
                "Sí"
            )


            if key not in existing:

                features.append(
                    {
                        "listing_id":
                            listing_id,

                        "category":
                            "Comodidades y equipamiento",

                        "feature":
                            item,

                        "value":
                            "Sí"
                    }
                )


    # --------------------------------------------------------
    # TIMESTAMP FEATURES
    # --------------------------------------------------------

    now = datetime.now()


    for feature in features:

        feature[
            "listing_type"
        ] = listing_type


        feature[
            "scraped_at"
        ] = now


    # --------------------------------------------------------
    # FEATURE DICT
    # --------------------------------------------------------

    feature_dict = features_to_dict(
        features
    )


    # --------------------------------------------------------
    # VARIABLES ESTRUCTURALES
    # --------------------------------------------------------

    structural = extract_structural_fields(
        feature_dict,
        highlighted_specs
    )


    # --------------------------------------------------------
    # UNITS
    # --------------------------------------------------------

    units = []


    if listing_type == "development":

        units = extract_development_units(
            driver,
            listing_id
        )


    # --------------------------------------------------------
    # POI
    # --------------------------------------------------------

    pois = extract_poi(
        driver,
        listing_id
    )


    # --------------------------------------------------------
    # RESULTADO PROPERTY
    # --------------------------------------------------------

    property_row = {

        "listing_id":
            listing_id,

        "url":
            url,

        "title":
            title,

        "subtitle":
            subtitle,

        "listing_type":
            listing_type,

        "price":
            price,

        "currency":
            currency,

        "address":
            address,

        "description":
            description,

        "seller_name":
            seller[
                "seller_name"
            ],

        "seller_id":
            seller[
                "seller_id"
            ],

        "seller_verified":
            seller[
                "seller_verified"
            ],

        # ----------------------------------------------------
        # VARIABLES ESTRUCTURALES
        # ----------------------------------------------------

        "total_m2_min":
            structural[
                "total_m2_min"
            ],

        "total_m2_max":
            structural[
                "total_m2_max"
            ],

        "construction_m2_min":
            structural[
                "construction_m2_min"
            ],

        "construction_m2_max":
            structural[
                "construction_m2_max"
            ],

        "bedrooms_min":
            structural[
                "bedrooms_min"
            ],

        "bedrooms_max":
            structural[
                "bedrooms_max"
            ],

        "bathrooms_min":
            structural[
                "bathrooms_min"
            ],

        "bathrooms_max":
            structural[
                "bathrooms_max"
            ],

        "parking_min":
            structural[
                "parking_min"
            ],

        "parking_max":
            structural[
                "parking_max"
            ],

        "age_years":
            structural[
                "age_years"
            ],

        # ----------------------------------------------------
        # METADATA DE EXTRACCIÓN
        # ----------------------------------------------------

        "n_features":
            len(features),

        "n_available_units":
            len(units),

        "n_poi":
            len(pois),

        "highlighted_specs_raw":
            json.dumps(
                highlighted_specs,
                ensure_ascii=False
            ),

        "characteristics_raw":
            json.dumps(
                feature_dict,
                ensure_ascii=False
            ),

        "ambientes_raw":
            json.dumps(
                ambientes,
                ensure_ascii=False
            ),

        "amenities_raw":
            json.dumps(
                amenities,
                ensure_ascii=False
            ),

        # ----------------------------------------------------
        # LINAGE STAGE 1
        # ----------------------------------------------------

        "search_municipality":
            row.get(
                "search_municipality",
                None
            ),

        "search_chunk":
            row.get(
                "search_chunk",
                None
            ),

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        "scrape_status":
            "success",

        "scrape_error":
            None,

        "scraped_at":
            now
    }


    return (
        property_row,
        features,
        units,
        pois
    )


# ============================================================
# LEER STAGE 1
# ============================================================

df = pd.read_csv(
    INPUT_FILE,
    dtype={
        "listing_id": str
    }
)


df[
    "listing_id"
] = (
    df[
        "listing_id"
    ]
    .apply(
        normalize_listing_id
    )
)


print(
    "\n"
    + "=" * 70
)


print(
    "STAGE 1 CARGADO"
)


print(
    "=" * 70
)


print(
    "\nShape:",
    df.shape
)


print(
    "Listings únicos:",
    df["listing_id"].nunique()
)


# ============================================================
# SELECCIONAR MUESTRA O FULL
# ============================================================

if TEST_MODE:

    sample_size = min(
        SAMPLE_SIZE,
        len(df)
    )


    df_run = df.sample(
        n=sample_size,
        random_state=RANDOM_STATE
    ).reset_index(
        drop=True
    )


    print(
        "\nMODO TEST"
    )


    print(
        "Listings seleccionados:",
        len(df_run)
    )


else:

    df_run = df.reset_index(
        drop=True
    )


    print(
        "\nMODO FULL"
    )


    print(
        "Listings a procesar:",
        len(df_run)
    )


# ============================================================
# RECUPERAR CHECKPOINTS
# ============================================================

properties = []
features = []
units = []
pois = []


if RESUME:

    properties = load_existing(
        OUTPUT_PROPERTIES
    )


    features = load_existing(
        OUTPUT_FEATURES
    )


    units = load_existing(
        OUTPUT_UNITS
    )


    pois = load_existing(
        OUTPUT_POI
    )


    print(
        "\nCheckpoint existente:"
    )


    print(
        "Properties:",
        len(properties)
    )


    print(
        "Features:",
        len(features)
    )


    print(
        "Units:",
        len(units)
    )


    print(
        "POI:",
        len(pois)
    )


# ============================================================
# IDS YA EXITOSOS
# ============================================================

successful_ids = set()


for row in properties:

    if (
        row.get("scrape_status")
        == "success"
    ):

        listing_id = normalize_listing_id(
            row.get("listing_id")
        )


        if listing_id:

            successful_ids.add(
                listing_id
            )


# ============================================================
# SELENIUM
# ============================================================

driver = webdriver.Chrome()

driver.maximize_window()


wait = WebDriverWait(
    driver,
    TIMEOUT
)


# ============================================================
# CONTADORES
# ============================================================

success_count = 0
error_count = 0
skip_count = 0


# ============================================================
# LOOP PRINCIPAL
# ============================================================

try:

    for index, row in df_run.iterrows():

        listing_id = normalize_listing_id(
            row[
                "listing_id"
            ]
        )


        print(
            "\n\n"
            + "=" * 70
        )


        print(
            f"LISTING "
            f"{index + 1}/"
            f"{len(df_run)} "
            f"| MLM-{listing_id}"
        )


        print(
            "=" * 70
        )


        # ====================================================
        # SKIP SI YA FUE EXITOSO
        # ====================================================

        if (
            RESUME
            and
            listing_id
            in successful_ids
        ):

            skip_count += 1


            print(
                "↪ Ya procesado correctamente. SKIP."
            )


            continue


        # ====================================================
        # BORRAR VERSIONES VIEJAS DE ESTE LISTING
        # ====================================================

        properties = remove_listing(
            properties,
            listing_id
        )


        features = remove_listing(
            features,
            listing_id
        )


        units = remove_listing(
            units,
            listing_id
        )


        pois = remove_listing(
            pois,
            listing_id
        )


        try:

            (
                property_row,
                listing_features,
                listing_units,
                listing_pois
            ) = process_listing(
                driver,
                wait,
                row
            )


            # ------------------------------------------------
            # AGREGAR
            # ------------------------------------------------

            properties.append(
                property_row
            )


            features.extend(
                listing_features
            )


            units.extend(
                listing_units
            )


            pois.extend(
                listing_pois
            )


            success_count += 1


            successful_ids.add(
                listing_id
            )


            # ------------------------------------------------
            # LOG
            # ------------------------------------------------

            print(
                "✓ SUCCESS"
            )


            print(
                "Tipo:",
                property_row[
                    "listing_type"
                ]
            )


            print(
                "Título:",
                property_row[
                    "title"
                ]
            )


            print(
                "Precio:",
                property_row[
                    "price"
                ],
                property_row[
                    "currency"
                ]
            )


            print(
                "Total m²:",
                property_row[
                    "total_m2_min"
                ],
                "-",
                property_row[
                    "total_m2_max"
                ]
            )


            print(
                "Construcción m²:",
                property_row[
                    "construction_m2_min"
                ],
                "-",
                property_row[
                    "construction_m2_max"
                ]
            )


            print(
                "Recámaras:",
                property_row[
                    "bedrooms_min"
                ],
                "-",
                property_row[
                    "bedrooms_max"
                ]
            )


            print(
                "Baños:",
                property_row[
                    "bathrooms_min"
                ],
                "-",
                property_row[
                    "bathrooms_max"
                ]
            )


            print(
                "Features:",
                property_row[
                    "n_features"
                ]
            )


            print(
                "Unidades:",
                property_row[
                    "n_available_units"
                ]
            )


            print(
                "POIs:",
                property_row[
                    "n_poi"
                ]
            )


        # ====================================================
        # ERROR DEL LISTING
        # ====================================================

        except Exception as e:

            error_count += 1


            error_text = (
                f"{type(e).__name__}: "
                f"{str(e)}"
            )


            print(
                "✗ ERROR"
            )


            print(
                error_text
            )


            properties.append(
                {
                    "listing_id":
                        listing_id,

                    "url":
                        row.get(
                            "url",
                            None
                        ),

                    "title":
                        row.get(
                            "title",
                            None
                        ),

                    "listing_type":
                        None,

                    "price":
                        None,

                    "currency":
                        None,

                    "address":
                        None,

                    "description":
                        None,

                    "seller_name":
                        None,

                    "seller_id":
                        None,

                    "seller_verified":
                        None,

                    "total_m2_min":
                        None,

                    "total_m2_max":
                        None,

                    "construction_m2_min":
                        None,

                    "construction_m2_max":
                        None,

                    "bedrooms_min":
                        None,

                    "bedrooms_max":
                        None,

                    "bathrooms_min":
                        None,

                    "bathrooms_max":
                        None,

                    "parking_min":
                        None,

                    "parking_max":
                        None,

                    "age_years":
                        None,

                    "n_features":
                        0,

                    "n_available_units":
                        0,

                    "n_poi":
                        0,

                    "highlighted_specs_raw":
                        None,

                    "characteristics_raw":
                        None,

                    "ambientes_raw":
                        None,

                    "amenities_raw":
                        None,

                    "search_municipality":
                        row.get(
                            "search_municipality",
                            None
                        ),

                    "search_chunk":
                        row.get(
                            "search_chunk",
                            None
                        ),

                    "scrape_status":
                        "error",

                    "scrape_error":
                        error_text,

                    "scraped_at":
                        datetime.now()
                }
            )


        # ====================================================
        # CHECKPOINT DESPUÉS DE CADA LISTING
        # ====================================================

        processed_since_checkpoint = 0

        if processed_since_checkpoint >= CHECKPOINT_EVERY:
            
            save_all(
                properties,
                features,
                units,
                pois
            )
        
            print(
                f"\nCheckpoint guardado "
                f"({CHECKPOINT_EVERY} listings procesados)."
            )
    
        processed_since_checkpoint = 0


        print(
            f"Success nuevos: "
            f"{success_count}"
            f" | Errors: "
            f"{error_count}"
            f" | Skips: "
            f"{skip_count}"
        )


        # Pausa conservadora
        time.sleep(
            SLEEP_BETWEEN_LISTINGS
        )


# ============================================================
# INTERRUPCIÓN MANUAL
# ============================================================

except KeyboardInterrupt:

    print(
        "\n\nProceso detenido manualmente."
    )


# ============================================================
# ERROR SELENIUM GENERAL
# ============================================================

except WebDriverException as e:

    print(
        "\n\nError general de Selenium:"
    )


    print(
        repr(e)
    )


# ============================================================
# FINAL
# ============================================================

finally:

    if (index + 1) % 25 == 0:
        save_all(
            properties,
            features,
            units,
            pois
        )
        print(
            "\nCheckpoint guardado.")


    driver.quit()


    print(
        "\n\n"
        + "=" * 70
    )


    print(
        "STAGE 2 POC TERMINADO"
    )


    print(
        "=" * 70
    )


    print(
        "\nProperties:",
        len(properties)
    )


    print(
        "Features:",
        len(features)
    )


    print(
        "Development units:",
        len(units)
    )


    print(
        "POIs:",
        len(pois)
    )


    print(
        "\nSuccess nuevos:",
        success_count
    )


    print(
        "Errors:",
        error_count
    )


    print(
        "Skipped por resume:",
        skip_count
    )


    print(
        "\nOutputs:"
    )


    print(
        " -",
        OUTPUT_PROPERTIES
    )


    print(
        " -",
        OUTPUT_FEATURES
    )


    print(
        " -",
        OUTPUT_UNITS
    )


    print(
        " -",
        OUTPUT_POI
    )


    # ========================================================
    # RESUMEN DE FEATURES
    # ========================================================

    if features:

        df_features = pd.DataFrame(
            features
        )


        if "feature" in df_features.columns:

            print(
                "\n"
                + "=" * 70
            )


            print(
                "TOP 25 FEATURES ENCONTRADAS"
            )


            print(
                "=" * 70
            )


            print(
                df_features[
                    "feature"
                ]
                .value_counts()
                .head(25)
            )


    print(
        "\nChrome cerrado."
    )
    
    
    
    
    
df = pd.read_csv("stage2_properties_test.csv")

print(df["listing_type"].value_counts(dropna=False))

print(
    df.loc[
        df["scrape_status"] == "error",
        ["listing_id", "scrape_error"]
    ]
)
