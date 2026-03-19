import feedparser
import json
import requests
import cloudscraper
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
from dateutil import parser
from urllib.parse import urljoin, urlparse
import time
import random
import os
import ssl
import shutil
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.ssl_ import create_urllib3_context
from requests.packages.urllib3.poolmanager import PoolManager

# Selenium Imports for robust fallback
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️ Selenium modules not found. Install 'selenium' and 'webdriver-manager' for better results.")

# --- CONFIGURATION ---
# Format: ("Blog Name", "Feed URL", ["SPECIAL_TAGS"])

TOP_BLOGGERS = [
    ("PlantYou", "https://plantyou.com/feed/", ["WFPB"]),#html scrapping was not working
    ("Mary's Test Kitchen", "https://www.marystestkitchen.com/feed/", []), #She can stay here - do not need all of her back catalog
    ("Jessica in the Kitchen", "https://jessicainthekitchen.com/feed", []),#html scrapping was not working
    ("Justine Cooks Vegan", "https://justinecooksvegan.com/feed/",[]),
    #("Mouthwatering Vegan", "https://www.mouthwateringvegan.com/feed/",[]),
    ("Yup It's Vegan", "https://yupitsvegan.com/feed/",[]),
    ("Forks Over Knives", "https://www.forksoverknives.com/all-recipes/feed", ["WFPB"]),
    ("Gimme Some Oven (Vegan Recipes)", "https://www.gimmesomeoven.com/dietary/vegan/feed/",[]),
    ("ZardyPlants", "https://zardyplants.com/feed/", ["WFPB", "Budget"]),
    ("Justine Snacks (Vegan Recipes)", "https://justinesnacks.com/category/special-diets/vegan/feed/", []),
    ("Sweet Potato Soul", "https://sweetpotatosoul.com/feed/",[]),
    ("A Couple Cooks (Vegan Recipes)", "https://www.acouplecooks.com/tag/vegan/feed/",[]),
    ("Fragrant Vanilla Cake", "https://www.fragrantvanilla.com/feed/",[]),
    ("Pinch of Yum (Vegan Recipes)", "https://pinchofyum.com/recipes/vegan/feed", []),
    ("Watch Learn Eat", "https://watchlearneat.com/vegan-recipes/feed/", ["Easy"]), 
    ("Dr. Vegan", "https://drveganblog.com/feed/", ["Easy"]),
    ("Make It Dairy Free", "https://makeitdairyfree.com/feed/",[]), 
    ("Rainbow Nourishments", "https://www.rainbownourishments.com/feed/",[]), 
    ("Connoisseurus Veg", "https://www.connoisseurusveg.com/feed/",[]),
    ("The Little Blog of Vegan", "https://www.thelittleblogofvegan.com/feed/",[]),
    ("Holistic Chef Academy", "https://holisticchefacademy.com/feed/", []),
    ("The Banana Diaries", "https://thebananadiaries.com/feed/", []),
    #("Vegan Recipe Club", "https://www.veganrecipeclub.org.uk/feed/", []),
    #("Messy Vegan Cook", "https://messyvegancook.com/feed/", []),
    ("Full of Plants", "https://fullofplants.com/feed/", []),
    ("Ambitious Kitchen (Vegan Recipes)", "https://www.ambitiouskitchen.com/feed/?diettypes=vegan", []),
    ("My Darling Vegan", "https://www.mydarlingvegan.com/feed/", []),
    ("From My Bowl", "https://frommybowl.com/feed/", []),
    ("The First Mess", "https://thefirstmess.com/feed/", []),
    ("A Virtual Vegan", "https://avirtualvegan.com/feed/", []),
    ("The Hidden Veggies", "https://thehiddenveggies.com/feed/", ["Budget"]),
    ("The Full Helping (Vegan Recipes)", "https://www.thefullhelping.com/feed/", []),
    ("Lazy Cat Kitchen", "https://www.lazycatkitchen.com/feed/", []),
    ("Flora & Vino", "https://www.floraandvino.com/feed/", ["WFPB"]),
    ("Sarah's Vegan Kitchen", "https://sarahsvegankitchen.com/feed/", []),
    ("The Foodie Takes Flight", "https://thefoodietakesflight.com/feed/", ["Easy"]),
    ("Eat Figs, Not Pigs", "https://www.eatfigsnotpigs.com/feed/", []),
    ("Plant Power Couple", "https://www.plantpowercouple.com/feed/", ["Easy"]),
    #("Ann Arbor Vegan Kitchen", "https://annarborvegankitchen.com/feed/", ["WFPB"]),
    ("The Conscious Plant Kitchen", "https://www.theconsciousplantkitchen.com/feed/", []),
    ("NutritionFacts.org", "https://nutritionfacts.org/topics/recipes/feed/", ["WFPB"]),
    ("Strength and Sunshine", "https://strengthandsunshine.com/feed/", ["Easy", "GF"]),
    ("Vegan Heaven", "https://veganheaven.org/feed/", []),
    ("The Plant-Based RD", "https://plantbasedrdblog.com/feed/", []),
    ("Rabbit and Wolves", "https://www.rabbitandwolves.com/feed/", []),
    ("Plant Baes", "https://plantbaes.com/feed/", []),
    ("The Stingy Vegan", "https://thestingyvegan.com/feed/", ["Easy", "Budget"]),
    ("The Vegan 8", "https://thevegan8.com/feed/", ["Easy", "Budget"]),
    ("Chef Bai", "https://www.chefbai.kitchen/blog?format=rss", []),
    #("Big Box Vegan", "https://bigboxvegan.com/feed/", []),
    ("Veggiekins", "https://veggiekinsblog.com/feed/", ["Easy", "GF"]),
    ("HealthyGirl Kitchen", "https://healthygirlkitchen.com/feed/", []),
    ("Monkey & Me Kitchen Adventures", "https://monkeyandmekitchenadventures.com/feed/", []),
    ("Vegan in the Freezer", "https://veganinthefreezer.com/feed/", []),
    ("Running on Real Food", "https://runningonrealfood.com/feed/", ["WFPB"]),
    ("Elavegan", "https://elavegan.com/feed/", ["GF"]),
    ("Earth to Veg", "https://earthtoveg.com/feed/", []),
    ("Unconventional Baker", "https://www.unconventionalbaker.com/feed/", ["GF"]),
    ("One Arab Vegan", "https://www.onearabvegan.com/feed/", []),
    ("Love and Lemons (Vegan Recipes)", "https://www.loveandlemons.com/category/recipes/vegan/feed/", []),
    ("Healthy Little Vittles", "https://healthylittlevittles.com/feed/", ["GF"]),
    ("The Korean Vegan", "https://thekoreanvegan.com/feed/", []),
    ("Vegan Richa", "https://www.veganricha.com/feed/", []),
    ("Rainbow Plant Life GF", "https://rainbowplantlife.com/diet/gluten-free/feed/", ["GF"]),
    ("Rainbow Plant Life", "https://rainbowplantlife.com/feed/", []),
    ("Dreena Burton", "https://dreenaburton.com/feed/", ["WFPB"]),
    ("Nora Cooks", "https://www.noracooks.com/feed/", []),
    #("Baking Hermann", "https://bakinghermann.com/feed/", []),
    ("Vegan Richa GF", "https://www.veganricha.com/category/gluten-free/feed/", ["GF"]),
    ("The Edgy Veg", "https://www.theedgyveg.com/feed/", []),
    ("Cookie and Kate (Vegan Recipes)", "https://cookieandkate.com/category/food-recipes/vegan/feed/", []),
    #("BOSH! TV", "https://www.bosh.tv/feed/", []),
    ("Simple Vegan Blog", "https://simpleveganblog.com/feed/", []),
    ("Hot For Food", "https://www.hotforfoodblog.com/feed/", []),
    ("My Goodness Kitchen", "https://mygoodnesskitchen.com/feed/", []),
    #("VegNews", "https://vegnews.com/feed", []),
    ("Sweet Simple Vegan", "https://sweetsimplevegan.com/feed/", []),
    ("Bianca Zapatka", "https://biancazapatka.com/en/feed/", []),
    #("The Cheap Lazy Vegan", "https://thecheaplazyvegan.com/feed/", ["Budget", "Easy"]),
    ("It Doesn't Taste Like Chicken", "https://itdoesnttastelikechicken.com/feed/", []),
    ("The Post-Punk Kitchen", "https://www.theppk.com/feed/", []),
    ("Steamy Vegan", "https://steamyvegan.com/feed/", []),
    ("Healthier Steps", "https://healthiersteps.com/feed/", []),
    ("Choosing Chia (Vegan Recipes)", "https://choosingchia.com/category/diet/vegan/feed/", ["Easy"]),
    ("Cadry's Kitchen", "https://cadryskitchen.com/feed/", []),
    ("Plant-Based on a Budget", "https://plantbasedonabudget.com/feed/", ["Budget"]),
    ("Namely Marly", "https://namelymarly.com/category/vegan-recipes/feed/", []),
    ("Gretchen's Vegan Bakery", "https://www.gretchensveganbakery.com/feed/", []),
    ("Vegan Yack Attack", "https://veganyackattack.com/feed/", []),
    ("The Burger Dude", "https://theeburgerdude.com/feed/", []),
    ("My Vegan Minimalist", "https://myveganminimalist.com/feed/", []),
    ("Addicted to Dates", "https://addictedtodates.com/feed/", []),
    ("Rhian's Recipes", "https://www.rhiansrecipes.com/feed/", ["GF"]),
]

DISRUPTORS = []

# --- DIRECT HTML SCRAPING SOURCES ---

HTML_SOURCES = [
    ("Pick Up Limes", ("https://www.pickuplimes.com/recipe/?sb=&public=on&page={}", 1, 1), [], "custom_pul"),#not able to do RSS feed on this one
    
#("Justine Cooks Vegan", ("https://justinecooksvegan.com/category/recipes/page/{}//", 1, 1),[], "wordpress"),
#("Mouthwatering Vegan", "https://www.mouthwateringvegan.com/recipes/",[], "wordpress"),
#("Yup It's Vegan", ("https://yupitsvegan.com/page/{}/?s=+", 1, 1),[], "wordpress"),
   #("Forks Over Knives", "https://www.forksoverknives.com/all-recipes/", ["WFPB"], "wordpress"),#maxed out
    #("Gimme Some Oven (Vegan Recipes)", ("https://www.gimmesomeoven.com/dietary/vegan/page/{}/", 1, 1), [], "wordpress"),
        #("ZardyPlants", ("https://zardyplants.com/category/recipes/page/{}/", 1, 1), ["WFPB", "Budget"], "wordpress"),
    ("High Carb Hannah", ("https://highcarbhannah.co/pages/recipes?page={}", 1, 1), [], "wordpress"),
    #("SO VEGAN", "https://www.wearesovegan.com/recipes", [], "squarespace"),
    ("The Whole Food Plant Based Cooking Show", ("https://plantbasedcookingshow.com/category/recipes/page/{}/", 1, 1), ["WFPB"], "wordpress"),
        #("Justine Snacks (Vegan Recipes)", ("https://justinesnacks.com/category/special-diets/vegan/page/{}/", 1, 1),[], "wordpress"),
                    #("Sweet Potato Soul", ("https://sweetpotatosoul.com/category/recipes/page/{}/", 1, 1), [], "wordpress"),
        #("A Couple Cooks (Vegan Recipes)", ("https://www.acouplecooks.com/tag/vegan/?_paged={}", 1, 1),[], "wordpress"),
     #("Fragrant Vanilla Cake", ("https://www.fragrantvanilla.com/page/{}/?s=+", 1, 1), [], "wordpress"),
       # ("Pinch of Yum (Vegan Recipes)", ("https://pinchofyum.com/recipes/vegan/page/{}/?hl=en-US", 1, 1),[], "wordpress"),
    #("Watch Learn Eat", ("https://watchlearneat.com/vegan-recipes/page/{}/", 1, 1), ["Easy"], "wordpress"),#6
        #("Dr. Vegan", ("https://drveganblog.com/page/{}/?s=+", 1, 1), ["Easy"], "wordpress"),#21..not working for squarespace
            #("Make It Dairy Free", ("https://makeitdairyfree.com/recipe-filter/?sf_paged={}", 1, 1), [], "wordpress"),#23
            #("Rainbow Nourishments", ("https://www.rainbownourishments.com/page/{}/?s=+", 1, 1), [], "wordpress"),#27
      #("Connoisseurus Veg", ("https://www.connoisseurusveg.com/category/entrees/page/{}/", 1, 1), [], "wordpress"),#28 
        #("The Little Blog of Vegan", ("https://www.thelittleblogofvegan.com/tag/recipes/page/{}", 1, 1), [], "wordpress"),
            #("Holistic Chef Academy", ("https://holisticchefacademy.com/page/{}/?s=+", 1, 1), [], "wordpress"),#6
  #  ("The Banana Diaries", ("https://thebananadiaries.com/page/{}/", 1, 1), [], "squarespace"),#123 pages
        #("Vegan Recipe Club", ("https://www.veganrecipeclub.org.uk/recipes/?sf_paged={}", 6, 16),[], "wordpress"),
            # She was too messy ("Messy Vegan Cook",("https://messyvegancook.com/category/all-recipes/page/{}/", 1, 9), [], "wordpress"),#9
   # ("Full of Plants", ("https://fullofplants.com/recipes/page/{}/", 1, 1), [], "wordpress"),#12 pages
        #("Ambitious Kitchen (Vegan Recipes)", ("https://www.ambitiouskitchen.com/recipe-index/?_sft_diettypes=vegan&sf_paged={}", 1, 1),[], "wordpress"),
         #("My Darling Vegan", ("https://www.mydarlingvegan.com/page/{}/?s=+&cuisine=&meal=&diet=&ingredient%5B0%5D=", 1, 1), [], "wordpress"),
        #("From My Bowl", ("https://frommybowl.com/category/diet/vegan/page/{}/", 1, 1), [], "wordpress"),#35 pages
    #("The First Mess", ("https://thefirstmess.com/page/{}/?s=+", 1, 1), [], "wordpress"),#not sure how many
        #("A Virtual Vegan", ("https://avirtualvegan.com/category/archives/page/{}/", 1, 1), [], "wordpress"),#14 pages
    #("The Hidden Veggies", ("https://thehiddenveggies.com/recipe-index/page/{}/", 1, 1), ["Budget"], "squarespace"),#52 pages #fix this one#fix this one#fix this one#fix this one#fix this one#fix this one#fix this one#fix this one#fix this one#fix this one
    #("The Full Helping (Vegan Recipes)",("https://www.thefullhelping.com/dietary/vegan/page/{}/", 1, 1), [],"wordpress"),#Load more so unsure how many pages
    #("Lazy Cat Kitchen", ("https://www.lazycatkitchen.com/category/recipes/page/{}/", 1, 1), [], "wordpress"),#38 pages
    #("Flora & Vino", ("https://www.floraandvino.com/category/all-food-recipes/page/{}/", 1, 1), ["WFPB"], "wordpress"),#82 pages
    #("Sarah's Vegan Kitchen", ("https://sarahsvegankitchen.com/category/recipes/page/{}/", 1, 1), [], "wordpress"),#16 pages
    #("The Foodie Takes Flight", ("https://thefoodietakesflight.com/category/all-recipes/page/{}/", 1, 1), ["Easy"], "wordpress"),#42 pages
    #("Eat Figs, Not Pigs", ("https://www.eatfigsnotpigs.com/page/{}/?s=+", 1, 1), [], "wordpress"),#42 pages
    #("Plant Power Couple", ("https://www.plantpowercouple.com/page/{}/?s=+", 1, 2), ["Easy"], "wordpress"),#37 pages
    ("Ann Arbor Vegan Kitchen", ("https://annarborvegankitchen.com/blog/page/{}/", 1, 1), ["WFPB"], "wordpress"),#about 35 pages
    #("The Conscious Plant Kitchen", ("https://www.theconsciousplantkitchen.com/category/recipes/?_paged={}/feed/", 1, 1), [], "wordpress"),#22 pages
    #("NutritionFacts.org", "https://nutritionfacts.org/recipes", ["WFPB"], "wordpress"),#all on one page
    #("Strength and Sunshine", ("https://strengthandsunshine.com/page/{}/?s=+", 1, 1), ["Easy", "GF"], "wordpress"), #280 pages
    #("Vegan Heaven", ("https://veganheaven.org/category/all-recipes/page/{}/", 1, 1), [], "wordpress"),#49 pages
   # #("The Plant-Based RD", ("https://plantbasedrdblog.com/category/blog-posts/page/{}/", 1, 1), [], "wordpress"),#12 pages
    #("Rabbit and Wolves", ("https://www.rabbitandwolves.com/category/vegan-entree-recipes/page/{}/", 1, 1), [], "wordpress"),#51 pages of entrees (first category so far)
    #("Plant Baes", ("https://plantbaes.com/category/recipes/?_paged={}", 1, 1), [], "squarespace"),#22 pages...worked last time
    #("The Stingy Vegan", ("https://thestingyvegan.com/page/{}/?s=+", 1, 1), ["Easy", "Budget"], "wordpress"),#22 pages
    #("The Vegan 8", ("https://thevegan8.com/page/{}/?s=+", 1, 1), ["Easy", "Budget"], "wordpress"),#65 pages
    #("Chef Bai", "https://www.chefbai.kitchen/blog", [], "wordpress"),
    #("Big Box Vegan", ("https://bigboxvegan.com/category/recipes/page/{}/", 1, 1), [], "wordpress"),#43 pages
   #("Veggiekins", ("https://veggiekinsblog.com/category/eat/gluten-free/page/{}/", 1, 1), ["Easy","GF"], "wordpress"), # GF only for now. she has others
    #("HealthyGirl Kitchen", ("https://healthygirlkitchen.com/category/recipes/page/{}/", 1, 1), [], "wordpress"),#6 pages
    #("Monkey & Me Kitchen Adventures", ("https://monkeyandmekitchenadventures.com/category/recipes/page/{}/", 1, 1), [], "wordpress"),#not sure pages
    #("Vegan in the Freezer", ("https://veganinthefreezer.com/recipes/?pg={}", 1, 1), [], "wordpress"),#62 pages
   # ("Running on Real Food", ("https://runningonrealfood.com/category/recipes/page/{}/", 1, 1), ["WFPB"], "wordpress"),#45 pages
    #("Elavegan", ("https://elavegan.com/category/recipe/page/{}/", 1, 1), ["GF"], "wordpress"), #51 pages
   # ("Earth to Veg", "https://earthtoveg.com/page/1/?s=+", [], "wordpress"),#maxed out
    #("Unconventional Baker", "https://www.unconventionalbaker.com/", ["GF"], "wordpress"),
    #("One Arab Vegan", ("https://www.onearabvegan.com/category/recipes/page/{}/", 1, 1), [], "wordpress"),#28 pages
    #("Love and Lemons (Vegan Recipes)", ("https://www.loveandlemons.com/category/recipes/vegan/page/{}/", 1, 1), [], "wordpress"),#75 or more pages
   # ("Healthy Little Vittles", ("https://healthylittlevittles.com/page/{}/?s=+", 6, 10), ["GF"], "wordpress"), #17 pages
   # ("The Korean Vegan", ("https://thekoreanvegan.com/recipes/?pg={}", 1, 1), [], "wordpress"),#maxed
   # ("Vegan Richa", ("https://www.veganricha.com/recipes-with-facets/?fwp_paged={}",1, 1), [], "wordpress"), #119 pages
   # ("Rainbow Plant Life GF", "https://rainbowplantlife.com/diet/gluten-free/", ["GF"], "wordpress"),#maxed out
   # ("Rainbow Plant Life", ("https://rainbowplantlife.com/category/recipes/page/{}/", 1, 1), [], "wordpress"),#19 pages
    #("Dreena Burton", ("https://dreenaburton.com/category/recipes/page/{}/", 1, 1), ["WFPB"], "wordpress"),#21 pages of this
   #("Nora Cooks", "https://www.noracooks.com/blog/page/1/", [], "wordpress"),#maxed out
   ("Baking Hermann", "https://bakinghermann.com/recipes/", [], "hermann"), #have gotten all of this catalog
   # ("Vegan Richa GF", "https://www.veganricha.com/category/gluten-free/", ["GF"], "wordpress"),
   # ("The Edgy Veg", ("https://www.theedgyveg.com/recipes/page/{}/", 1, 1), [], "wordpress"),#75 pages
   # ("Cookie and Kate (Vegan Recipes)", "https://cookieandkate.com/category/food-recipes/vegan/", [], "wordpress"),#maxed out
    ("BOSH! TV", "https://www.bosh.tv/recipes", [], "wordpress"), #maxed out
    #("Simple Vegan Blog", "https://simpleveganblog.com/", [], "wordpress"),#maxed
   # ("Hot For Food","https://www.hotforfoodblog.com/category/recipes/page/1/",[],"wordpress"),#maxed out
   # ("My Goodness Kitchen", "https://mygoodnesskitchen.com/recipes/page/1/", [], "wordpress"),
   ("VegNews", ("https://vegnews.com/recipes/page/{}/", 1, 1), [], "wordpress"),#maybe infinite pages lol
   # ("Sweet Simple Vegan", "https://sweetsimplevegan.com/recipes/page/1/", [], "wordpress"),#maxed out recipes
   # ("Bianca Zapatka", ("https://biancazapatka.com/en/recipes/page/{}/", 1, 1), [], "wordpress"),#70 pages, input as a range
    ("The Cheap Lazy Vegan", ("https://thecheaplazyvegan.com/blog/page/{}/", 1, 1), ["Budget", "Easy"], "wordpress"),#62 pages
   # ("It Doesn't Taste Like Chicken", "https://itdoesnttastelikechicken.com/recipe-index/", [], "wordpress"),#ma
   # ("The Post-Punk Kitchen", "https://www.theppk.com/", [], "wordpress"),#should get all of their recipes with this special link
   # ("Steamy Vegan", ("https://steamyvegan.com/page/{}/?s=+", 1, 1), [], "wordpress"), #16 paages
   # ("Healthier Steps", ("https://healthiersteps.com/recipe-index/?_paged={}", 1, 1), [], "wordpress"),#Hundreds of pages for this one
   # ("Choosing Chia (Vegan Recipes)", ("https://choosingchia.com/category/diet%20/vegan/page/{}/", 1, 1), ["Easy"], "wordpress"),#37 pages
   # ("Cadry's Kitchen", ("https://cadryskitchen.com/page/{}/?s=+", 1, 1), [], "wordpress"),
   # ("Plant-Based on a Budget", "https://plantbasedonabudget.com/recipes", ["Budget"], "wordpress"),#17 pages
  #  ("Namely Marly", ("https://namelymarly.com/category/vegan-recipes/page/{}/", 1, 1), [], "wordpress"),#35 pages for this
   # ("Gretchen's Vegan Bakery", ("https://www.gretchensveganbakery.com/category/all-recipes/page/{}/", 1, 1), [], "wordpress"),#at least 50 pages
   # ("Vegan Yack Attack", "https://veganyackattack.com/", [], "wordpress"),#maxed out recipes. keep base link for new ones
   ("Minimalist Baker (Vegan Recipes)", "https://minimalistbaker.com/recipes/vegan", [], "wordpress"),#maxed out recipes
   # ("The Burger Dude", "https://theeburgerdude.com/recipe%20index/page/1/", [], "wordpress"),#maxed out
   # ("My Vegan Minimalist", ("https://myveganminimalist.com/page/{}/?s=+", 1, 1), [], "wordpress"),
   # ("Addicted to Dates", ("https://addictedtodates.com/category/recipes/page/{}/", 1, 1), [], "wordpress"),#19 pages
   # ("Rhian's Recipes", "https://www.rhiansrecipes.com/recipes", ["GF"], "wordpress") #maxed out
   ("Reddit", "https://www.reddit.com/r/veganrecipes/new.rss", [], "custom_reddit"),
]

# --- DISPLAY NAME MAPPING ---
# Maps Internal Name -> Public Display Name
# Updated: We do NOT merge GF blogs back to main names anymore. 
# They will appear separately (e.g. "Rainbow Plant Life GF").
DISPLAY_NAME_MAP = {}

ALL_FEEDS = TOP_BLOGGERS + DISRUPTORS

# --- MAPS ---
URL_MAP = {}
BLOG_TAG_MAP = {}

# Process RSS Feeds
for item in ALL_FEEDS:
    if len(item) == 3:
        name, url, tags = item
        URL_MAP[name] = url
        BLOG_TAG_MAP[name] = tags
    else:
        print(f"⚠️ Warning: Skipping malformed RSS config: {item}")

# Process HTML Sources
for item in HTML_SOURCES:
    if len(item) == 4:
        name, url, tags, mode = item
        URL_MAP[name] = url
        BLOG_TAG_MAP[name] = tags
    else:
        print(f"⚠️ Warning: Skipping malformed HTML config: {item}")


MAX_RECIPES_PER_BLOG = 300
cutoff_date = datetime.now().astimezone() - timedelta(days=360)

# --- KEYWORDS FOR AUTO TAGGING ---
WFPB_KEYWORDS = [
    'oil-free', 'oil free', 'no oil', 'wfpb', 'whole food', 'clean', 'refined sugar free', 
    'sos-free', 'sos free', 'no added sugar', 'whole grain', 'unprocessed', 'sugar-free',
    'sugar free', 'salt-free', 'salt free', 'date sweetened', 'naturally sweetened'
]

EASY_KEYWORDS = [
    'easy', 'quick', 'simple', 'fast', '1-pot', 'one-pot', 'one pot', 'one bowl', 'one-bowl', 
    '1 pan', 'one pan', '30-minute', '15-minute', '20-minute', '10-minute', 'under 30', 'under 20',
    'under 15', '5-ingredient', '4-ingredient', '6-ingredient', 'sheet pan', 'skillet', 'mug', 
    'blender', 'no-bake', 'no bake', 'air fryer', 'instant pot', 'microwave', 'lazy', 'minimal',
    'fuss-free', 'fuss free', 'weeknight', 'meal prep', 'make-ahead', 'make ahead',
    '1-step', 'one-step', 'one step', '1 step'
]

BUDGET_KEYWORDS = [
    'budget', 'budget-friendly', 'budget friendly', 'cheap', 'frugal', 'economical', 'pantry', 
    'pantry staples', 'low cost', 'money saving', 'affordable', 'leftover', 'scraps', 'student', 
    'canned', 'bulk', 'cost-effective', 'inexpensive', 'thrifty'
]

GF_KEYWORDS = [
    'gluten-free', 'gluten free', 'glutenfree', 'gf', 'wheat-free', 'flourless', 'almond flour', 
    'oat flour', 'rice flour', 'grain-free', 'grain free', 'coconut flour', 'chickpea flour', 
    'buckwheat', 'tapioca', 'cassava', 'celiac', 'coeliac', 'sorghum', 'teff', 'arrowroot'
]

# Words that usually indicate a recipe is NOT Gluten-Free (unless explicitly stated)
NON_GF_KEYWORDS = [
    'seitan', 'vital wheat gluten', 'wheat', 'barley', 'rye', 'couscous', 'farro', 
    'spelt', 'bulgur', 'semolina', 'udon', 'beer', 'malt', 'panko', 'kamut', 'einkorn', 
    'orzo', 'durum', 'graham', 'soy sauce', 'freekeh', 'wheatberries', 'wheat berries', 
    'triticale', 'brewer\'s yeast', 'malt extract', 'malt syrup', 'malt vinegar'
]
    
NON_RECIPE_KEYWORDS = [
    # Listicles / Roundups
    "roundup", "collection", "favorites", "best of", "top 10", "top 20", " 2026", "top 5", "22 ", "20 ",
    " best vegan ", " dinner ideas", " lunch ideas", " breakfast ideas", " meal prep ideas",
    " ways to ", " things to ", "must make", "must have", "must try", " recipes for ", 
    " recipes to ", " ideas for ", "why ", "guide", "recipes ",

    # Reddit: Product & Ingredient Reviews
    "y'all weren't lying", "weren't lying", "taste test", "tastes just like", 
    "store bought", "store-bought", "has anyone tried", "has anyone bought", 
    "found this", "trader joe", " tjs ", "aldi", "whole foods", "beyond meat", 
    "impossible meat", "egg white powder", "brand of", "what brand", "are ", "need ",
    
    # Reddit: Methods, Hacks & General Discussions
    "game changer", "game-changer", "thoughts on", "unpopular opinion", "debate", 
    "rant", "psa:", "did you know", "appreciation post", "new here", "thank you",
    
    # Reddit: Help, Troubleshooting & Requests
    "help me", "need help", "please help", "question:", "quick question", 
    "advice", "suggestions for", "looking for", " iso ", "recommend", 
    "recommendations", "what went wrong", "what am i doing wrong", "how do i", 
    "what do you use", "what's the best", "can i substitute", "substitute for",
    
    # Reddit: Fails (Successes usually have recipes in comments, but fails don't)
    "fail", "ruined", "disaster", "tastes awful", "tastes bad", "throw it out"
    
    # Meal Plans & Diaries
    "meal plan", "weekly menu", "menu plan", "what i eat", "what i ate", "wiaw", 
    "grocery haul", "batch cooking plan", "meal prep plan",
    
    # Blog/Life Updates & Chit Chat
    "life lately", "coffee talk", "saturday sun", "link love", "weekend reading", 
    "my story", "journey", "routine", "travel", "city guide", "where to eat", 
    "dining out", "restaurant", "kitchen tour", "behind the scenes", "vlog", "recap", 
    "q&a", "podcast", "episode", "janelle carss", "rpl", "obama", "trump", "reading list",
    
    # Products / Promotions / Books
    "cookbook", "gift guide", "merch", "ebook", "discount", "coupon", "promo", 
    "black friday", "cyber monday", " sale ", "giveaway", "contest", "winner", 
    "best seller", "appliances",
    
    # Educational / Guides (Not specific recipes)
    " 101", "tutorial", "guide to", " tips ", " tricks ", "faq", "how to cut", "how to store", 
    "how to freeze", "substitutes", "benefits of", " vs ", "difference between",
    
    # Admin / Website & Reviews
    "review", "interview", "guest post", "workshop", "class", "course", 
    "announcement", "update", "news", "policy", "terms", "privacy", "contact", 
    "about me", "search", "sitemap", "disclaimer", "headshot"
]

# --- ADVANCED SCRAPER SETUP & SSL FIX ---

class LegacySSLAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        ctx = create_urllib3_context()
        ctx.load_default_certs()
        try:
            ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        except Exception:
            ctx.set_ciphers('DEFAULT')
        self.poolmanager = PoolManager(num_pools=connections, maxsize=maxsize, block=block, ssl_context=ctx)

scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
# Mount to both protocols to handle redirects gracefully
scraper.mount('https://', LegacySSLAdapter())
scraper.mount('http://', LegacySSLAdapter())

fallback_session = requests.Session()
fallback_session.mount('https://', LegacySSLAdapter())
fallback_session.mount('http://', LegacySSLAdapter())
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15'
]

def get_headers(referer=None):
    h = {'User-Agent': random.choice(USER_AGENTS)}
    if referer:
        h['Referer'] = referer
    return h

def get_auto_tags(title):
    tags = []
    t_lower = title.lower()
    if any(k in t_lower for k in WFPB_KEYWORDS): tags.append("WFPB")
    if any(k in t_lower for k in EASY_KEYWORDS): tags.append("Easy")
    if any(k in t_lower for k in BUDGET_KEYWORDS): tags.append("Budget")
    if any(k in t_lower for k in GF_KEYWORDS): tags.append("GF")
    return tags

def is_pet_recipe(title):
    t = title.lower()
    pet_phrases = ['dog treat', 'cat treat', 'dog biscuit', 'cat biscuit', 'dog food', 'cat food', 'pup treat', 'kitty treat', 'dog cookie']
    if any(phrase in t for phrase in pet_phrases): return True
    return False

def fetch_with_selenium(url):
    """
    Last resort fetcher using Headless Chrome.
    Updated for 2026: Anti-detection, Eager Loading, and Explicit Waits.
    """
    if not SELENIUM_AVAILABLE:
        return None

    try:
        print(f"   [Selenium] Attempting fallback for {url}...")
        chrome_options = Options()
        
        # 1. Modern Headless Mode
        chrome_options.add_argument("--headless=new")
        
        # 2. Performance & Stability
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080") # Ensure desktop layout
        chrome_options.add_argument("--log-level=3")
        
        # 3. Anti-Detection / Stealth (Crucial for blocking evasion)
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        # 4. User Agent Rotation
        chrome_options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
        
        # 5. Page Load Strategy: 'eager' 
        # Waits for DOMContentLoaded (HTML+Scripts) but not all images/CSS. Much faster.
        chrome_options.page_load_strategy = 'eager'

        service = Service(ChromeDriverManager().install())
        driver = None
        
        try:
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Remove navigator.webdriver flag (Anti-detection)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            driver.set_page_load_timeout(30)
            
            driver.get(url)
            
            # 6. Explicit Wait logic instead of fixed sleep
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                time.sleep(2) 
            except Exception:
                pass 

            return driver.page_source
        except Exception as e:
            print(f"   [!] Selenium Driver Error: {str(e)[:100]}")
            return None
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    except Exception as e:
        print(f"   [!] Selenium failed: {str(e)[:100]}")
    
    return None

def robust_fetch(url, is_binary=False, is_scraping_page=False):
    if is_scraping_page:
        time.sleep(random.uniform(2, 5)) 
    
    headers = get_headers(referer="https://www.google.com/")

    # 1. CloudScraper (Timeout 15s)
    try:
        response = scraper.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.content if is_binary else response.text
    except Exception as e:
        print(f"   [!] Cloudscraper error for {url}: {str(e)[:50]}")
    
    # 2. Requests Fallback (Timeout 15s)
    try:
        fallback_session.headers.update(headers)
        response = fallback_session.get(url, timeout=15)
        if response.status_code == 200:
            return response.content if is_binary else response.text
    except Exception as e:
        print(f"   [!] Requests error for {url}: {str(e)[:50]}")

    # 3. Selenium Fallback (Only for text/HTML, not binary images)
    if not is_binary:
        return fetch_with_selenium(url)
        
    return None

def fetch_og_image(link):
    try:
        html = robust_fetch(link, is_scraping_page=True)
        if not html: return None
        soup = BeautifulSoup(html, 'lxml')
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'): return og_image['content']
        twitter_image = soup.find('meta', name='twitter:image')
        if twitter_image and twitter_image.get('content'): return twitter_image['content']
    except Exception:
        return None
    return None

def extract_image(entry, blog_name, link):
    image_candidate = None
    
    # 1. RSS Media Enclosures (Best source)
    if 'media_content' in entry:
        for media in entry.media_content:
            if 'url' in media: return media['url']
    if 'media_thumbnail' in entry: 
        return entry.media_thumbnail[0]['url']
        
    # 2. Parse HTML Content
    content = entry.get('content', [{}])[0].get('value', '') or entry.get('summary', '')
    if content:
        soup = BeautifulSoup(content, 'lxml')
        images = soup.find_all('img')
        
        for img in images:
            # Check for high-res source in srcset first
            srcset = img.get('srcset') or img.get('data-srcset')
            src = parse_srcset(srcset)
            
            # Fallback to standard attributes
            if not src:
                src = (img.get('data-src') or img.get('data-lazy-src') or img.get('data-original') or img.get('src'))
            
            if not src: continue
            
            # Filter out junk/placeholders
            src_lower = src.lower()
            if any(x in src_lower for x in ['pixel', 'emoji', 'icon', 'logo', 'gravatar', 'gif', 'facebook', 'pinterest', 'share', 'button', 'loader', 'placeholder', 'blank.jpg', '1x1']): 
                continue
                
            width = img.get('width')
            if width and width.isdigit() and int(width) < 200: continue
            
            image_candidate = src
            break
            
    # 3. Fallback to OpenGraph (Last resort)
    if not image_candidate or "placeholder" in str(image_candidate):
        image_candidate = fetch_og_image(link)
        
    return image_candidate if image_candidate else "icon.jpg"

def inject_static_html(recipes):
    """Injects the top 60 recipes into index.html <noscript> for massive SEO/crawlability gains."""
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        start_marker = '<!-- SEO_STATIC_START -->'
        end_marker = '<!-- SEO_STATIC_END -->'
        
        if start_marker in html and end_marker in html:
            top_recipes = recipes[:60]
            links_html = ""
            for r in top_recipes:
                safe_title = r['title'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                links_html += f'\n                <a href="{r["link"]}">{safe_title} ({r["blog_name"]})</a><br>'
            
            new_html = html[:html.find(start_marker) + len(start_marker)] + "\n" + links_html + "\n                " + html[html.find(end_marker):]
            
            with open('index.html', 'w', encoding='utf-8') as f:
                f.write(new_html)
            print("✅ Injected static SEO links into index.html")
    except Exception as e:
        print(f"⚠️ Could not inject static HTML: {e}")
        
def generate_sitemap(recipes):
    now = datetime.now().strftime("%Y-%m-%d")
    
    # High-value category URLs for Google to index
    seo_paths = [
        "",
        "?type=meal",
        "?type=sweet",
        "?tag=GF",
        "?tag=WFPB",
        "?tag=Easy",
        "?tag=Budget",
        "?tag=Protein",
        "?cuisine=American",
        "?cuisine=Indian",
        "?cuisine=Mexican",
        "?cuisine=Italian",
        "?cuisine=Asian",
        "?cuisine=Mediterranean"
    ]
    
    url_nodes = ""
    for path in seo_paths:
        priority = "1.0" if path == "" else "0.8"
        url_nodes += f"""   <url>
      <loc>https://searchveg.com/{path.replace('&', '&amp;')}</loc>
      <lastmod>{now}</lastmod>
      <changefreq>daily</changefreq>
      <priority>{priority}</priority>
   </url>\n"""

    sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{url_nodes}</urlset>"""
    
    with open('sitemap.xml', 'w') as f:
        f.write(sitemap_content)
    print("Generated sitemap.xml with category pages")

def generate_llms_txt(recipes):
    """Generates a robust llms.txt for AI/LLM indexing and GEO optimization."""
    count = len(recipes)
    sources_count = len(set(r['blog_name'] for r in recipes))
    last_updated = datetime.now().strftime("%Y-%m-%d")

    txt_content = f"""# Find Veg Dish (AI Context)

## Project Overview
searchveg.com is a curated, real-time aggregator of high-quality plant-based, vegan, and gluten-free recipes. It actively monitors {sources_count} distinct food blogs and chefs to provide a centralized feed of the latest vegan culinary content.

## Dataset Statistics
- **Total Recipes:** {count}
- **Last Updated:** {last_updated}
- **Content Types:** 100% Vegan. Includes Whole Food Plant Based (WFPB), Gluten-Free (GF), Budget-Friendly, and Easy/Quick recipes.

## Primary Sources
We aggregate content from verified sources including:
- Minimalist Baker
- Rainbow Plant Life
- Pick Up Limes
- Nora Cooks
- Vegan Richa
- And {sources_count - 5} others.

## Schema & Structure
Recipes are structured with:
- Title
- Source Blog Name
- Direct Link
- Thumbnail Image
- Published Date
- Special Tags (WFPB, GF, Easy, Budget)

## Access Points
- **Main Feed:** https://searchveg.com/
- **Sitemap:** https://searchveg.com/sitemap.xml
- **RSS Feed:** (Coming Soon)

## Usage
This file is intended to help Large Language Models (LLMs) understand the structure, freshness, and authority of the content on searchveg.com for better indexing and answer generation regarding vegan recipes.
"""
    with open('llms.txt', 'w') as f:
        f.write(txt_content)
    print("Generated robust llms.txt")

# --- HELPER FUNCTIONS FOR ROBUST HTML PARSING ---

def parse_srcset(srcset_str):
    """Parses a srcset string and returns the URL with the highest width."""
    if not srcset_str:
        return None
    
    candidates = []
    # Split by comma, handling potential commas in URLs is tricky but srcset standard helps
    parts = srcset_str.split(',')
    
    for p in parts:
        p = p.strip()
        if not p: continue
        
        # Split by space. Last part is usually width descriptor.
        subparts = p.split()
        if len(subparts) < 2:
             # Just a URL, assume width 0 or check if it's just a url
             if subparts: candidates.append((0, subparts[0]))
             continue
        
        url_part = subparts[0]
        width_part = subparts[-1]
        
        # Parse width
        width = 0
        if width_part.endswith('w'):
            try: width = int(width_part[:-1])
            except: pass
        elif width_part.endswith('x'):
            try: width = float(width_part[:-1]) * 1000 # Rough equivalent for density
            except: pass
            
        candidates.append((width, url_part))
        
    if not candidates: 
        return None
    
    # Sort by width desc
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]

def extract_metadata_from_page(url):
    """
    Fetches a specific recipe page to extract the precise date and high-res image.
    Used for new items that are missing data in the archive view.
    """
    html = robust_fetch(url, is_scraping_page=True)
    if not html: return None, None
    
    soup = BeautifulSoup(html, 'lxml')
    date_obj = None
    image_url = None

    # 1. Date Extraction
    # Strategy A: JSON-LD (Most reliable)
    scripts = soup.find_all('script', type='application/ld+json')
    for script in scripts:
        if not script.string: continue
        try:
            data = json.loads(script.string)
            nodes = []
            if isinstance(data, list): nodes = data
            elif isinstance(data, dict): nodes = data.get('@graph', [data])
            
            for node in nodes:
                # Look for Article or Recipe
                if node.get('@type') in ['Article', 'BlogPosting', 'Recipe', 'NewsArticle']:
                    dt = node.get('datePublished') or node.get('dateCreated')
                    if dt:
                        try:
                            date_obj = parser.parse(dt)
                            break
                        except: pass
            if date_obj: break
        except: continue

    # Strategy B: Meta Tags
    if not date_obj:
        meta_date = soup.find('meta', property='article:published_time') or \
                    soup.find('meta', property='og:updated_time') or \
                    soup.find('meta', itemprop='datePublished')
        if meta_date and meta_date.get('content'):
            try: date_obj = parser.parse(meta_date['content'])
            except: pass
            
    # Strategy C: Time Tags
    if not date_obj:
        time_tag = soup.find('time')
        if time_tag:
            dt_str = time_tag.get('datetime') or time_tag.get_text()
            try: date_obj = parser.parse(dt_str)
            except: pass

    # 2. Image Extraction (High Res)
    # OpenGraph is usually best for the main image
    og_img = soup.find('meta', property='og:image')
    if og_img and og_img.get('content'):
        image_url = og_img['content']
        
    return date_obj, image_url


# --- HTML SCRAPING LOGIC ---

def scrape_html_feed(name, url, mode, existing_links, recipes_list, source_tags):
    time.sleep(random.uniform(5, 8)) # Safety delay
    
    # --- REDDIT SPECIAL HANDLER ---
    # Pro-tip: Reddit blocks generic browser scrapers heavily. We bypass by using a custom API User-Agent.
    if mode == "custom_reddit":
        headers = {'User-Agent': 'searchveg-recipe-bot/1.0 (by /u/scraper)'}
        try:
            r = requests.get(url, headers=headers, timeout=15)
            html = r.text
        except Exception as e:
            print(f"   [!] Reddit fetch failed: {e}")
            html = None
    else:
        html = robust_fetch(url, is_scraping_page=True)
    
    # --- BAKING HERMANN SPECIAL HANDLER ---
    # If standard fetch fails for Hermann, try a fallback session
    if mode == "custom_hermann" and not html:
        try:
            print(f"   [Combine] Trying insecure fetch for {url}...")
            # Use a fresh session with verification disabled (fixes Webflow/SSL issues)
            s = requests.Session()
            s.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            })
            r = s.get(url, timeout=20, verify=False)
            if r.status_code == 200:
                html = r.text
        except Exception as e:
            print(f"   [!] Hermann insecure fetch failed: {e}")

    if not html:
        return [], "❌ Blocked/HTML Fail"
    
    found_items = []
    
    # Skip BeautifulSoup parsing if we are handling a JSON API like Reddit
    if mode == "custom_reddit":
        soup = None
    else:
        soup = BeautifulSoup(html, 'lxml')
    
    # --- MODE 1: WORDPRESS / GENERIC AGGREGATION ---
    if mode == "wordpress":
        # 1. Scope to Main Content
        main_scope = soup.find('main') or \
                     soup.find(id='main') or \
                     soup.find(class_='site-main') or \
                     soup.find(id='content') or \
                     soup.find(class_='entry-content') or \
                     soup.find(class_='elementor-location-archive') or \
                     soup.find(class_='archive-container')
        
        if not main_scope: main_scope = soup

        # 2. Link Aggregation
        candidates = {} # URL -> {'title': str, 'image': str}

        all_links = main_scope.find_all('a', href=True)

        for a in all_links:
            raw_link = a['href']
            
            # Clean Link
            if any(x in raw_link for x in ['#', 'javascript:', 'mailto:', 'tel:', '/category/', '/tag/', '/author/', '/page/', '?share=', 'comment', '#comments']):
                continue
            
            full_link = urljoin(url, raw_link)
            if full_link.rstrip('/') == url.rstrip('/'): continue # Skip home link

            if full_link not in candidates:
                candidates[full_link] = {'title': '', 'image': None}

            # 2a. IMAGE EXTRACTION (Standard + Background)
            img = a.find('img')
            src = None
            
            if img:
                # 1. Try to get largest image from srcset
                srcset = img.get('srcset') or img.get('data-srcset')
                if srcset:
                    src = parse_srcset(srcset)
                
                # 2. Fallback to standard attributes if srcset failed
                if not src:
                    src = img.get('data-src') or img.get('data-lazy-src') or img.get('src')

            # Check for CSS Background Image (Fix for Zacchary Bird / Vegan Punks / Full Helping)
            if not src:
                style_source = a if a.has_attr('style') else a.find(style=True)
                if style_source and style_source.has_attr('style'):
                    style_str = style_source['style']
                    if 'background-image' in style_str and 'url(' in style_str:
                        try:
                            src = style_str.split('url(')[1].split(')')[0].strip('"').strip("'")
                        except: pass
            
            if src:
                # Clean up URL (remove query params for resizing if needed, though usually fine)
                candidates[full_link]['image'] = src

            # 2b. TITLE EXTRACTION
            link_text = a.get_text(" ", strip=True)
            h_child = a.find(['h2', 'h3', 'h4'])
            
            if h_child:
                candidates[full_link]['title'] = h_child.get_text(strip=True)
            elif len(link_text) > 10 and len(link_text) > len(candidates[full_link]['title']):
                # Filter utility links
                if not any(x == link_text.lower() for x in ['read more', 'continue reading', 'get the recipe', 'view recipe', 'cookie policy']):
                    candidates[full_link]['title'] = link_text

        # 3. Process Candidates
        for link_url, data in candidates.items():
            if not data['title']: continue
            
            t_low = data['title'].lower()
            if len(data['title']) < 5: continue
            if any(x in t_low for x in ['privacy policy', 'contact', 'about us', 'terms', 'accessibility', 'skip to content']): continue

            if (link_url, name) in existing_links: continue

            final_image = data['image']
            deep_date = None
            
            deep_date, deep_image = extract_metadata_from_page(link_url)
            
            if deep_image: 
                final_image = deep_image
            
            if not final_image: 
                continue

            final_date = deep_date if deep_date else datetime(2020, 1, 1).replace(tzinfo=timezone.utc)
            
            if final_image and not final_image.startswith('http'):
                final_image = urljoin(url, final_image)

            found_items.append({
                "blog_name": name,
                "title": data['title'],
                "link": link_url,
                "image": final_image,
                "date": final_date.isoformat(),
                "is_disruptor": False,
                "special_tags": list(source_tags)
            })
            existing_links.add((link_url, name))

    # --- MODE 2: SQUARESPACE (NEW) ---
    elif mode == "squarespace":
        # Targets: Standard 7.0/7.1 Blog Lists, Summary Blocks, Grid Items
        items = soup.select("article, .summary-item, .blog-item, .blog-basic-grid-item, .entry, .h-entry")
        
        for item in items:
            # 1. Find the link
            a_tag = item.select_one("a.summary-title-link, a.blog-item-title-link, .entry-title a, a.u-url")
            
            # Fallback: First link in container (usually the image link if title link is missing)
            if not a_tag: 
                a_tag = item.find('a', href=True)
            
            if not a_tag: continue
            
            href = a_tag['href']
            link = urljoin(url, href)
            
            # Filter non-recipe links (common in squarespace footers/navs if selector leaked)
            if any(x in link for x in ["/category/", "/tag/", "/author/", "/archive"]): continue

            if (link, name) in existing_links: continue

            # 2. Find Title
            # Try specific title classes first
            t_tag = item.select_one(".summary-title, .blog-item-title, .entry-title, h1, h2")
            title = t_tag.get_text(strip=True) if t_tag else a_tag.get_text(strip=True)
            
            if not title: title = "Recipe"

            # 3. Find Image (Squarespace uses data-src for lazy loading)
            img = item.find('img')
            image_candidate = None
            if img:
                image_candidate = img.get('data-src') or img.get('data-image') or img.get('src')
            
            # 4. Deep Fetch (Mandatory for Squarespace Dates & High Res Images)
            # Squarespace list views often hide dates or use weird formatting. 
            # We fetch the article page to get clean JSON-LD metadata.
            deep_date, deep_image = extract_metadata_from_page(link)
            
            final_image = deep_image if deep_image else image_candidate
            
            # 5. Fallback Date Logic
            # If deep fetch failed to find a date, default to a generic past date 
            # so it doesn't appear as "Brand New" on top of the feed.
            final_date = deep_date if deep_date else datetime(2022, 1, 1).replace(tzinfo=timezone.utc)

            if final_image:
                found_items.append({
                    "blog_name": name, 
                    "title": title, 
                    "link": link, 
                    "image": final_image,
                    "date": final_date.isoformat(), 
                    "is_disruptor": False, 
                    "special_tags": list(source_tags)
                })
                existing_links.add((link, name))

    # --- MODE 2: CUSTOM PUL (Pick Up Limes) ---
    elif mode == "custom_pul":
        links = soup.find_all('a')
        for a in links:
            href = a.get('href', '')
            if '/recipe/' in href and href != '/recipe/':
                if a.find('img'):
                    link = urljoin("https://www.pickuplimes.com", href)
                    if (link, name) in existing_links: continue
                    t_tag = a.select_one("h3, h2, .article_title") 
                    title = t_tag.get_text(strip=True) if t_tag else "Recipe"
                    img_tag = a.find('img')
                    image = img_tag.get('src') if img_tag else "icon.jpg"
                    
                    # FIX: Force metadata extraction to get real date
                    deep_date, deep_image = extract_metadata_from_page(link)
                    if deep_image: image = deep_image
                    
                    # If date not found, use old date to prevent "new at top" issue
                    final_date = deep_date if deep_date else datetime(2022, 1, 1).replace(tzinfo=timezone.utc)

                    found_items.append({
                        "blog_name": name, "title": title, "link": link, "image": image,
                        "date": final_date.isoformat(), "is_disruptor": False, "special_tags": list(source_tags)
                    })
                    existing_links.add((link, name))

    # --- MODE 3: CUSTOM ZJ (Zucker & Jagdwurst) ---
    elif mode == "custom_zj":
        # Specific selector for their teaser cards to avoid navigation links
        links = soup.select(".teaser__link, article a") or soup.find_all('a', href=True)
        for a in links:
            href = a.get('href', '')
            # Filter valid recipe posts (ignoring archives, pages, categories)
            if '/en/' in href and not any(x in href for x in ['/archive', '/page/', '/category/', '/about', '/search', 'shop']):
                link = urljoin(url, href)
                if (link, name) in existing_links: continue

                # Title: Try finding header inside, or fallback to text
                t_tag = a.select_one("h2, h3, .teaser__title, .headline")
                title = t_tag.get_text(strip=True) if t_tag else "Recipe"
                
                # IMAGE STRATEGY:
                # ZJ uses aggressive lazy loading on the archive page (often blank/placeholder).
                # We skip the local image check and mandatory Deep Fetch the article page 
                # to get the robust OpenGraph image.
                deep_date, deep_image = extract_metadata_from_page(link)
                
                found_items.append({
                    "blog_name": name, 
                    "title": title, 
                    "link": link, 
                    "image": deep_image if deep_image else "icon.jpg",
                    # Default to slightly newer date fallback to ensure visibility if date fetch fails
                    "date": deep_date.isoformat() if deep_date else datetime(2023,1,1).replace(tzinfo=timezone.utc).isoformat(),
                    "is_disruptor": False, 
                    "special_tags": list(source_tags)
                })
                existing_links.add((link, name))

    # --- MODE 3a: CUSTOM VEGAN HUGGS (Trellis Theme) ---
    elif mode == "custom_veganhuggs":
        # Targets Trellis/Mediavine structure: <article> tags with specific classes
        articles = soup.find_all('article')
        for art in articles:
            # Title Link
            title_tag = art.find(['h2', 'h3'], class_='entry-title') or art.find(['h2', 'h3'], class_='post-summary__title')
            a_tag = title_tag.find('a') if title_tag else art.find('a', href=True)
            
            if not a_tag: continue
            
            link = a_tag['href']
            if (link, name) in existing_links: continue
            
            title = a_tag.get_text(strip=True)
            
            # Image: Look for img tag or data-bg
            img = art.find('img')
            image = None
            if img:
                image = img.get('data-src') or img.get('data-lazy-src') or img.get('src')
            
            # Deep fetch for clean date
            deep_date, deep_image = extract_metadata_from_page(link)
            
            found_items.append({
                "blog_name": name, "title": title, "link": link, 
                "image": deep_image if deep_image else (image or "icon.jpg"),
                "date": deep_date.isoformat() if deep_date else datetime(2022,1,1).replace(tzinfo=timezone.utc).isoformat(),
                "is_disruptor": False, "special_tags": list(source_tags)
            })
            existing_links.add((link, name))

    # --- MODE 3b: CUSTOM NO MEAT DISCO (Squarespace 7.1 Grid) ---
    elif mode == "custom_nomeatdisco":
        # Targets Squarespace 7.1 .grid-item structure
        items = soup.select(".grid-item, .blog-basic-grid-item")
        for item in items:
            a_tag = item.find('a', class_='grid-item-link') or item.find('a', href=True)
            if not a_tag: continue
            
            href = a_tag['href']
            link = urljoin(url, href)
            if (link, name) in existing_links: continue
            
            # Title
            title_div = item.select_one(".grid-item-title, .blog-title, h3")
            title = title_div.get_text(strip=True) if title_div else "Recipe"
            
            # Image
            img = item.find('img')
            image = None
            if img:
                 image = img.get('data-src') or img.get('src')
            
            # Metadata
            deep_date, deep_image = extract_metadata_from_page(link)
            
            found_items.append({
                "blog_name": name, "title": title, "link": link, 
                "image": deep_image if deep_image else (image or "icon.jpg"),
                "date": deep_date.isoformat() if deep_date else datetime(2022,1,1).replace(tzinfo=timezone.utc).isoformat(),
                "is_disruptor": False, "special_tags": list(source_tags)
            })
            existing_links.add((link, name))

    # --- MODE 4: CUSTOM HERMANN (Improved for Webflow Lazy Loading) ---
    elif mode == "custom_hermann":
        # Baking Hermann
        # 1. Try finding items via standard classes
        candidates = soup.select(".w-dyn-item") + soup.select(".recipe-card") + soup.find_all('a', class_='recipe-link')
        
        # If robust_fetch failed to get content, soup might be empty.
        # But if we have soup, iterate:
        
        processed_urls = set()
        
        for item in candidates:
            a_tag = item if item.name == 'a' else item.find('a', href=True)
            if not a_tag: continue
            
            href = a_tag['href']
            if '/recipes/' not in href: continue
            
            link = urljoin("https://bakinghermann.com", href)
            if link in processed_urls or (link, name) in existing_links: continue
            processed_urls.add(link)

            title = "Recipe"
            t_elem = item.select_one("h3, h2, h4, .heading")
            if t_elem: title = t_elem.get_text(strip=True)
            elif item.get_text(strip=True): title = item.get_text(strip=True)[:50]
            
            # 2. IMAGE STRATEGY: Webflow often puts images in background-image styles or lazy-loaded img tags
            image_candidate = None
            
            # Check A: Background Image in Style
            style_elem = item.find(style=lambda v: v and 'background-image' in v) or \
                         (item.has_attr('style') and 'background-image' in item['style'] and item)
            
            if style_elem:
                try:
                    style = style_elem['style']
                    # Extract url('...')
                    if 'url(' in style:
                        image_candidate = style.split('url(')[1].split(')')[0].strip('"').strip("'")
                except: pass

            # Check B: Image tag with data-src (Webflow lazy load)
            if not image_candidate:
                img = item.find('img')
                if img:
                    image_candidate = img.get('src') or img.get('data-src') or img.get('srcset')
                    # If srcset, parse it
                    if image_candidate and ',' in image_candidate:
                        image_candidate = parse_srcset(image_candidate)

            # 3. Deep Fetch (Mandatory for Hermann to get Date)
            deep_date, deep_image = extract_metadata_from_page(link)
            
            final_image = deep_image if deep_image else image_candidate
            
            if final_image:
                found_items.append({
                    "blog_name": name, "title": title, "link": link, "image": final_image,
                    "date": deep_date.isoformat() if deep_date else datetime(2022,1,1).replace(tzinfo=timezone.utc).isoformat(),
                    "is_disruptor": False, "special_tags": list(source_tags)
                })
                existing_links.add((link, name))

    # --- MODE 5: CUSTOM REDDIT ---
    elif mode == "custom_reddit":
        try:
            feed = feedparser.parse(html)
            
            if not feed.entries:
                print("   [!] Reddit RSS returned no entries. Might be temporarily rate-limited.")
                return [], "❌ Reddit Empty"
                
            for entry in feed.entries:
                title = entry.get('title', 'Reddit Recipe')
                link = entry.get('link', '') # Link to the Reddit Post
                
                if not link or (link, name) in existing_links: 
                    continue
                
                content = entry.get('content', [{}])[0].get('value', '') or entry.get('summary', '')
                temp_soup = BeautifulSoup(content, 'lxml') if content else None
                
                # FILTER 1: NO EXTERNAL BLOG LINKS
                has_external_link = False
                if temp_soup:
                    links = temp_soup.find_all('a', href=True)
                    for a in links:
                        href = a['href'].lower()
                        # Allow internal Reddit links and standard image hosts. Block everything else (blogs/youtube)
                        allowed_domains = ['reddit.com', 'redd.it', 'imgur.com']
                        if not any(domain in href for domain in allowed_domains):
                            has_external_link = True
                            break
                            
                if has_external_link:
                    continue # Skip because it's linking to a blog
                
                # FILTER 2: NO QUESTIONS OR ADVICE REQUESTS
                title_lower = title.lower()
                if "?" in title:
                    continue
                if any(w in title_lower for w in ['help', 'request', 'iso', 'looking for', 'advice']):
                    continue
                
                # FILTER 3: MUST BE AN IMAGE POST OR CONTAIN RECIPE WORDS
                image = "icon.jpg"
                has_image = False
                
                if 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
                    image = entry.media_thumbnail[0]['url'].replace('&amp;', '&')
                    has_image = True
                elif temp_soup:
                    img_tag = temp_soup.find('img')
                    if img_tag and img_tag.get('src'):
                        src = img_tag['src'].replace('&amp;', '&')
                        # Ensure it's not just a tiny tracking pixel
                        if "width=" in src or "preview" in src or "format=" in src:
                            image = src
                            has_image = True
                
                # If there's no image, it's a text post. Verify it actually has recipe words.
                if not has_image:
                    content_lower = content.lower() if content else ""
                    recipe_keywords = ['ingredients', 'tsp', 'tbsp', 'cup ', 'cups ', 'instructions', 'method', 'yield:']
                    if not any(kw in content_lower for kw in recipe_keywords):
                        continue # Skip because it's just a text discussion, not a recipe
                
                # Date Parsing
                dt_str = entry.get('published', entry.get('updated', None))
                try:
                    dt = parser.parse(dt_str)
                    if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
                except:
                    dt = datetime.now(timezone.utc)
                
                # Success! Add the native Reddit recipe
                found_items.append({
                    "blog_name": name, 
                    "title": title, 
                    "link": link, 
                    "image": image,
                    "date": dt.isoformat(), 
                    "is_disruptor": False, 
                    "special_tags": list(source_tags)
                })
                existing_links.add((link, name))
                
        except Exception as e:
            print(f"   [!] Reddit RSS parsing failed: {e}")

    status = f"✅ OK ({len(found_items)})" if found_items else "⚠️ Scraped 0"
    return found_items, status
# --- MAIN EXECUTION ---

# 1. Load Existing Data
try:
    with open('data.json', 'r') as f:
        recipes = json.load(f)
        print(f"Loaded {len(recipes)} existing recipes.")
except (FileNotFoundError, json.JSONDecodeError):
    recipes = []
    print("No existing database found. Starting fresh.")

# 2. Cleanse Database
initial_count = len(recipes)
# Remove specific requested blogs
BLOGS_TO_REMOVE = []

recipes = [
    r for r in recipes 
    if not (r['blog_name'] == "VegNews" and "/recipes/" not in r['link'])
    and not any(rem.lower() in r['blog_name'].lower() for rem in BLOGS_TO_REMOVE)
]

# Update existing_links to be tuples of (link, blog_name) to allow separate entries for GF blogs
existing_links = {(r['link'], r['blog_name']) for r in recipes}

feed_stats = {}
previous_domain = ""

print(f"Fetching recipes from {len(ALL_FEEDS)} RSS feeds & {len(HTML_SOURCES)} HTML sources...", flush=True)

# 4. Scrape HTML Sources
print("::group::🕸️ Scraping HTML Sources", flush=True)
total_html = len(HTML_SOURCES)
for html_idx, item in enumerate(HTML_SOURCES, 1):
    start_time = time.time()  # <-- START TIMER
    
    if len(item) != 4: continue
    name, url_source, tags, mode = item
    
    print(f"[{html_idx}/{total_html}] Starting HTML Scrape: {name}", flush=True)
    
    # Enable Multi-Page Scraping: Handle string, list, OR range tuple
    if isinstance(url_source, tuple) and len(url_source) == 3:
        base_url, start_page, end_page = url_source
        urls_to_scrape = [base_url.format(i) for i in range(start_page, end_page + 1)]
    elif isinstance(url_source, list):
        urls_to_scrape = url_source
    else:
        urls_to_scrape = [url_source]
    
    all_new_items = []
    last_status = "Skipped"

    total_pages = len(urls_to_scrape)
    for i, single_url in enumerate(urls_to_scrape):
        if i == 0:
            time.sleep(random.uniform(2, 7))
        else:
            print(f"   ...cooling down (10s) before page {i+1}/{total_pages} of {name}...", flush=True)
            time.sleep(random.uniform(8, 12))

        try:
            print(f"   🔎 Page {i+1}/{total_pages} | HTML Scraping: {name} (Mode: {mode})...", flush=True)
            new_items, status = scrape_html_feed(name, single_url, mode, existing_links, recipes, tags)
            all_new_items.extend(new_items)
            last_status = status
            
            if "Blocked" in status or "Crash" in status:
                print(f"   Stopping multi-page scrape for {name} due to error on page {i+1}.", flush=True)
                break
                
        except Exception as e:
            print(f"   [!] Critical Error scraping {name}: {e}", flush=True)
            last_status = "❌ HTML Crash"

    recipes.extend(all_new_items)
    feed_stats[name] = {'new': len(all_new_items), 'status': last_status}

    # <-- STOP TIMER & PRINT
    elapsed = time.time() - start_time
    if elapsed < 60:
        time_str = f"{elapsed:.1f} seconds"
    else:
        time_str = f"{int(elapsed // 60)} minutes {int(elapsed % 60)} seconds"
    print(f"   ⏱️ Step took {time_str}\n", flush=True)

print("::endgroup::", flush=True)

# 4. Scrape HTML Sources
print("::group::🕸️ Scraping HTML Sources", flush=True)
total_html = len(HTML_SOURCES)
for html_idx, item in enumerate(HTML_SOURCES, 1):
    if len(item) != 4: continue
    name, url_source, tags, mode = item
    
    print(f"[{html_idx}/{total_html}] Starting HTML Scrape: {name}", flush=True)
    
    # Enable Multi-Page Scraping: Handle string, list, OR range tuple
    if isinstance(url_source, tuple) and len(url_source) == 3:
        base_url, start_page, end_page = url_source
        urls_to_scrape = [base_url.format(i) for i in range(start_page, end_page + 1)]
    elif isinstance(url_source, list):
        urls_to_scrape = url_source
    else:
        urls_to_scrape = [url_source]
    
    all_new_items =[]
    last_status = "Skipped"

    total_pages = len(urls_to_scrape)
    for i, single_url in enumerate(urls_to_scrape):
        if i == 0:
            time.sleep(random.uniform(2, 7))
        else:
            print(f"   ...cooling down (10s) before page {i+1}/{total_pages} of {name}...", flush=True)
            time.sleep(random.uniform(8, 12))

        try:
            print(f"   🔎 Page {i+1}/{total_pages} | HTML Scraping: {name} (Mode: {mode})...", flush=True)
            new_items, status = scrape_html_feed(name, single_url, mode, existing_links, recipes, tags)
            all_new_items.extend(new_items)
            last_status = status
            
            if "Blocked" in status or "Crash" in status:
                print(f"   Stopping multi-page scrape for {name} due to error on page {i+1}.", flush=True)
                break
                
        except Exception as e:
            print(f"   [!] Critical Error scraping {name}: {e}", flush=True)
            last_status = "❌ HTML Crash"

    recipes.extend(all_new_items)
    feed_stats[name] = {'new': len(all_new_items), 'status': last_status}

print("::endgroup::", flush=True)

print("::group::⚙️ Processing, Pruning & Saving", flush=True)

# 5. Backfill Tags (Including GF)
print("Updating tags for all recipes...", flush=True)
for recipe in recipes:
    bname = recipe['blog_name']
    current_tags = recipe.get('special_tags', []) 
    base_tags = list(BLOG_TAG_MAP.get(bname, []))
    auto_tags = get_auto_tags(recipe['title'])
    combined_tags = list(set(current_tags + base_tags + auto_tags))
    
    # SAFETY: Remove GF tag if title contains obvious gluten words
    if "GF" in combined_tags:
        t_lower = recipe['title'].lower()
        if any(kw in t_lower for kw in NON_GF_KEYWORDS):
            if not any(safe in t_lower for safe in GF_KEYWORDS):
                combined_tags.remove("GF")

    recipe['special_tags'] = combined_tags

# 5.2 Clean Recipe Titles
import re
print("Cleaning recipe titles...", flush=True)
# Comprehensive list of common scraping artifacts/junk from food blogs
PHRASES_TO_REMOVE = [
    "Continue Reading", "Continue", "Read More", "Read more »",
    "Get the Recipe", "View Recipe", "Click Here", "Click for Recipe",
    "Just the Recipe", "Jump to Recipe", "Skip to Recipe", "Skip to Content",
    "Print Recipe", "Print this Recipe", "Full Recipe Here", "Full Recipe",
    "Pin it for later", "Pin this Recipe", "Pin It", "Save for Later",
    "Share on Facebook", "Share this", "Click to Tweet",
    "Leave a Comment", "Leave a Reply", "Add a Comment", "Read Comments",
    "Recipe Card", "Ingredients", "Instructions", "Step-by-step", "Step by step",
    "Previous Post", "Next Post", "Older Posts", "Newer Posts", "Load More",
    "Watch the Video", "Watch Video", "Recipe Video"
]

# Sort by length descending so longer phrases are matched first (e.g. "Print this Recipe" before "Print Recipe")
PHRASES_TO_REMOVE.sort(key=len, reverse=True)

# Compiling regex to look for these phrases anywhere in the string, ignoring case
title_clean_pattern = re.compile(r'\b(' + '|'.join(re.escape(p) for p in PHRASES_TO_REMOVE) + r')\b', re.IGNORECASE)

for r in recipes:
    # 1. Strip out the bad phrases
    cleaned = title_clean_pattern.sub('', r['title'])
    
    # 2. Special check: Remove stray "(Video)" or "[Video]" or " - Video"
    cleaned = re.sub(r'\s*[\(\[\|\-]?\s*Video\s*[\)\]]?\s*$', '', cleaned, flags=re.IGNORECASE)
    
    # 3. Clean up any floating punctuation (e.g. "Title - " or " : Title") left behind at edges
    cleaned = re.sub(r'^[ \-\|:.,]+|[ \-\|:.,]+$', '', cleaned)
    
    # 4. Clean up accidental double spaces
    cleaned = re.sub(r'\s{2,}', ' ', cleaned).strip()
    
    # Apply the cleaned title, or fallback to original if cleaning accidentally emptied it
    r['title'] = cleaned if cleaned else r['title']

# 5.5 Global Non-Recipe Filter
print("Running global non-recipe filter...", flush=True)
non_recipes_removed_count = 0
valid_recipes = []

for r in recipes:
    title_lower = r['title'].lower()
    is_spam = False
    for kw in NON_RECIPE_KEYWORDS:
        if kw in title_lower:
            is_spam = True
            break
    
    if is_spam:
        non_recipes_removed_count += 1
    else:
        valid_recipes.append(r)

recipes = valid_recipes
print(f"   Removed {non_recipes_removed_count} non-recipe items.", flush=True)
    
# 6. Prune & Stats
print("Pruning database and calculating stats...", flush=True)
recipes_by_blog = {}
for r in recipes:
    bname = r['blog_name']
    if bname not in recipes_by_blog: recipes_by_blog[bname] = []
    recipes_by_blog[bname].append(r)

final_pruned_list = []
total_counts = {} 
latest_dates = {} 
wfpb_counts = {}
easy_counts = {}
budget_counts = {}
gf_counts = {}

for bname, blog_recipes in recipes_by_blog.items():
    blog_recipes.sort(key=lambda x: x['date'], reverse=True)
    if len(blog_recipes) > 0:
        latest_dates[bname] = blog_recipes[0]['date'][:10] 
    
    kept_recipes = blog_recipes[:MAX_RECIPES_PER_BLOG]
    final_pruned_list.extend(kept_recipes)
    total_counts[bname] = len(kept_recipes)
    wfpb_counts[bname] = sum(1 for r in kept_recipes if "WFPB" in r['special_tags'])
    easy_counts[bname] = sum(1 for r in kept_recipes if "Easy" in r['special_tags'])
    budget_counts[bname] = sum(1 for r in kept_recipes if "Budget" in r['special_tags'])
    gf_counts[bname] = sum(1 for r in kept_recipes if "GF" in r['special_tags'])

final_pruned_list.sort(key=lambda x: x['date'], reverse=True)

# --- GLOBAL DEDUPLICATION ---
print("   Running global deduplication (Rules: Title Match -> GF source > Older date)...", flush=True)
deduped_recipes = {}
for recipe in final_pruned_list:
    title = recipe['title']
    
    if title not in deduped_recipes:
        deduped_recipes[title] = recipe
    else:
        existing = deduped_recipes[title]
        curr_is_gf = "GF" in recipe['blog_name']
        exist_is_gf = "GF" in existing['blog_name']
        
        if curr_is_gf and not exist_is_gf:
            deduped_recipes[title] = recipe
        elif exist_is_gf and not curr_is_gf:
            pass 
        else:
            if recipe['date'] < existing['date']:
                deduped_recipes[title] = recipe

final_pruned_list = list(deduped_recipes.values())
final_pruned_list.sort(key=lambda x: x['date'], reverse=True)

print("Pruning complete. Saving database with distinct source names...", flush=True)

if len(final_pruned_list) > 50:
    temp_file = "data.tmp.json"
    final_file = "data.json"
    
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(final_pruned_list, f, indent=2)
        
        os.replace(temp_file, final_file)
        print(f"✅ Successfully wrote {len(final_pruned_list)} items to {final_file}", flush=True)
        
        inject_static_html(final_pruned_list)
        generate_sitemap(final_pruned_list)
        generate_llms_txt(final_pruned_list)
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR writing database: {e}", flush=True)
        if os.path.exists(temp_file):
            os.remove(temp_file)
else:
    print("⚠️ SAFETY ALERT: Database too small (<50 items). Skipping write to prevent data loss.", flush=True)

# 8. Generate Report
with open('FEED_HEALTH.md', 'w', encoding='utf-8') as f:
    f.write(f"# Feed Health Report\n")
    f.write(f"**Last Run:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    total_new_today = sum(stats.get('new', 0) for stats in feed_stats.values())
    total_in_db = len(final_pruned_list)
    all_monitored_names = set(list(feed_stats.keys()) + list(total_counts.keys()))
    total_blogs_monitored = len(all_monitored_names)
    
    active_sources_count = sum(1 for count in total_counts.values() if count >= 5)
    
    total_wfpb = sum(wfpb_counts.values())
    total_easy = sum(easy_counts.values())
    total_budget = sum(budget_counts.values())
    total_gf = sum(gf_counts.values())

    wfpb_percent = int((total_wfpb / total_in_db) * 100) if total_in_db > 0 else 0
    easy_percent = int((total_easy / total_in_db) * 100) if total_in_db > 0 else 0
    budget_percent = int((total_budget / total_in_db) * 100) if total_in_db > 0 else 0
    gf_percent = int((total_gf / total_in_db) * 100) if total_in_db > 0 else 0
    
    all_dates = [parser.parse(d) for d in latest_dates.values() if d != "N/A"]
    avg_date = datetime.fromtimestamp(sum(d.timestamp() for d in all_dates) / len(all_dates)).strftime('%Y-%m-%d') if all_dates else "N/A"

    f.write("### 📊 System Summary\n")
    f.write("| Metric | Value | Breakdown |\n")
    f.write("| :--- | :--- | :--- |\n")
    f.write(f"| **Total Database** | {total_in_db} | {total_new_today} new today |\n")
    f.write(f"| **Blogs Monitored** | {total_blogs_monitored} | {len(HTML_SOURCES)} HTML / {len(ALL_FEEDS)} RSS |\n")
    f.write(f"| **Active Sources** | {active_sources_count} | 5+ recipes |\n")
    f.write(f"| **WFPB / GF** | {total_wfpb} / {total_gf} | {wfpb_percent}% / {gf_percent}% |\n")
    f.write(f"| **Easy / Budget** | {total_easy} / {total_budget} | {easy_percent}% / {budget_percent}% |\n\n")

    f.write("---\n\n")
    f.write("### 📋 Detailed Blog Status (Sorted: 0 Recipes First)\n\n")
    
    f.write("| Blog Name | New | Total | WFPB | Easy | Budg | GF | Latest | Status |\n")
    f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
    
    report_rows = []
    for name in all_monitored_names:
        new = feed_stats.get(name, {}).get('new', 0)
        status = feed_stats.get(name, {}).get('status', 'Skipped')
        total = total_counts.get(name, 0)
        latest = latest_dates.get(name, "N/A")
        
        if "Scraped 0" in status or "Parsed 0 items" in status:
            status = "✅ OK" if total > 0 else "❌ Empty"
        
        report_rows.append({
            "name": name, "new": new, "total": total,
            "wfpb": wfpb_counts.get(name, 0), "easy": easy_counts.get(name, 0),
            "budget": budget_counts.get(name, 0), "gf": gf_counts.get(name, 0),
            "latest": latest, "status": status
        })

    report_rows.sort(key=lambda r: (1 if r['status'] == 'Skipped' else 0, r['total'], r['name']))

    for r in report_rows:
        f.write(f"| {r['name']} | {r['new']} | {r['total']} | {r['wfpb']} | {r['easy']} | {r['budget']} | {r['gf']} | {r['latest']} | {r['status']} |\n")

    f.write("\n---\n*Report generated automatically by searchveg.com Fetcher.*")

print(f"Successfully generated FEED_HEALTH.md with scrollable table. Database size: {len(final_pruned_list)}", flush=True)
print("::endgroup::", flush=True)
