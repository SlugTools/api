import webbrowser
from urllib.parse import parse_qs

dict = {
      "Breakfast": {
        "Breakfast": {
          "Chicken Apple Sausage": "400387*2*01", 
          "Hard-boiled Cage Free Egg (1)": "061003*1*01", 
          "Organic Oatmeal Gluten-Free": "031003*6*01", 
          "Sourdough French Toast": "217007*2*01", 
          "Soyrizo Tofu Scramble": "999880*4*01", 
          "Triangle Hash Brown Patty": "161003*2*01"
        }, 
        "Entrees": {
          "Cage-Free Scrambled Eggs": "061002*3*12"
        }, 
        "Clean Plate": {
          "Steamed Rice": "163000*4*16"
        }, 
        "Bakery": {
          "Apple Walnut Muffin": "023042*1*26", 
          "Assorted Scones": "189219*1*26", 
          "Muffin Blueberry Oat Bran": "213044*1*26"
        }
      }, 
      "Lunch": {
        "Breakfast": {
          "Chicken Apple Sausage": "400387*2*01", 
          "Sourdough French Toast": "217007*2*01", 
          "Soyrizo Tofu Scramble": "999880*4*01", 
          "Triangle Hash Brown Patty": "161003*2*01"
        }, 
        "Soups": {
          "Chicken Gumbo Soup": "701701*6*06", 
          "Organic Kale and Sweet Potato Soup": "899934*6*06"
        }, 
        "Grill": {
          "Allergen Free Halal Chicken Thigh": "020549*3 1/2*14", 
          "Cheeseburger": "400112*1*14", 
          "Regular Cut Fries": "161006*4*14", 
          "Tofu with Kosher Salt": "010226*4*14", 
          "Vegan Malibu Burger": "144081*1*14"
        }, 
        "Pizza": {
          "Cheese Pizza": "400082*1/12*15", 
          "Mexican Pizza with Chorizo": "141100*1/12*15"
        }, 
        "Clean Plate": {
          "Steamed Rice": "163000*4*16"
        }, 
        "Bakery": {
          "Lemon Loaf": "213041*1*26"
        }, 
        "Open Bars": {
          "Chicken Shoyu": "180132*5*30", 
          "Condiments": "060129*1*30", 
          "Steamed Rice": "163000*4*16", 
          "Steamed Seasonal Vegetables": "175071*3*30", 
          "Sweet & Sour Gardein Strips": "112012*4*30"
        }
      }, 
      "Dinner": {
        "Soups": {
          "Broccoli Cheese Soup": "022007*6*06", 
          "Organic Kale and Sweet Potato Soup": "899934*6*06"
        }, 
        "Entrees": {
          "ChickenTikka Masala": "180064*4*12", 
          "Masala Vegetables": "999850*3*12", 
          "Original Naan": "200006*1*12", 
          "Steamed Basmati Rice": "163023*3*12"
        }, 
        "Grill": {
          "Allergen Free Halal Chicken Thigh": "020549*3 1/2*14", 
          "Tofu with Kosher Salt": "010226*4*14"
        }, 
        "Pizza": {
          "Cheese Pizza": "400082*1/12*15", 
          "Mexican Pizza with Chorizo": "141100*1/12*15"
        }, 
        "Clean Plate": {
          "Steamed Rice": "163000*4*16"
        }, 
        "DH Baked": {
          "Apple Pie": "300074*1/10*24"
        }, 
        "Bakery": {
          "Chocolate S'more Pie": "212179*1*26"
        }, 
        "Open Bars": {
          "Battered Popcorn Chicken": "020590*3*30", 
          "Condiments": "060129*1*30", 
          "Mashed Potato Bowl Bar": "010109*1*30", 
          "Vegan Garlic Mashed Potatoes": "900062*4*30", 
          "Vegan Mushroom Gravy": "151002*2*30", 
          "Vegan Tenders": "184018*3*30"
        }
      }, 
      "Late Night": {
        "Entrees": {
          "Chickpea Curry with Tomato and Kale": "199995*3*12", 
          "Harissa Roasted Chicken": "030513*5*12", 
          "Roasted Seasonal Vegetables": "175073*3*12"
        }, 
        "Grill": {
          "Allergen Free Halal Chicken Thigh": "020549*3 1/2*14", 
          "Tofu with Kosher Salt": "010226*4*14"
        }, 
        "Pizza": {
          "Cheese Pizza": "400082*1/12*15", 
          "Mexican Pizza with Chorizo": "141100*1/12*15"
        }, 
        "Open Bars": {
          "BBQ Chicken": "868645*1*30", 
          "Condiments": "060129*1*30", 
          "Country Gravy": "020592*3*30", 
          "Garlic Mashed Yukon Golds": "161075*3*30", 
          "Mashed Potato Bowl Bar": "010109*1*30", 
          "Pork Carnitas": "187202*2*30", 
          "Roasted Corn": "171012*3*30", 
          "Vegan Tenders": "184018*3*30"
        }
      }
    }

webbrowser.register('firefox',
	None,
	webbrowser.BackgroundBrowser("C://Program Files//Mozilla Firefox//firefox.exe"))

for i in dict.keys():
  for j in dict[i].keys():
    for k in dict[i][j].keys():
      webbrowser.get('firefox').open(f"api.localhost:5000/items/{dict[i][j][k]}") 