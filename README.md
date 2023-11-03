#Example Screenshots inside screenshots folder

![](https://github.com/saiherng/ecommerce/blob/d60efda5009fad8864d97828e94738ac6b71f664/screenshots/1.%20Home%20Page.jpg)

# ecommerce
screenshots/1. Home Page.jpg
1) Open Terminal and activate the virtual environment. 

".\venv\Scritps\activate" - for Windows 

2) Install library requirements

"pip install -r requirements.txt"

2) Run app using python in terminal. Using python version 3.10.8

"python app.py"

3) Using browser, go to localhost:5000 or which ever port flask is currently using



All inputs and outputs to the APIs are done using Bootstrap UI for convenience.


Process for Creating Order
------------------------------------
1) Navigate to Customer Tab 
    i) Create new customer

2) Navigate to Orders Tab and scroll to the bottom
    i) Create order by specifing customer and vendor name
    ii) A new order entry would pop up on the specified vendor
    iii) Click on "View" button to check details

3) To add order items,
    i) select product from drop-down list.
    ii) specify quantity 
    iii) Click Create
    iv) A new order item entry would pop up 


Process for accessing secure api route
------------------------------------------------
1) First use the "localhost:5000/login" route to get an access token. 
2) Use Postman to input access token in the header for sample URI "localhost:5000/protected"
    
    key: Authentication
    value : Bearer "access_token"


BUGS 
-----------------------------------
1 - Having a hard time trying to find solution for deleting products without affecting existing order items.
2) Did not implement user sessions. Tried my best to focus on the crud operations.


