import requests
from bs4 import BeautifulSoup
import smtplib
import streamlit as st
import time
from threading import Thread


SENDER_EMAIL = 'user_email_id' 
SENDER_PASSWORD = 'App_password'        

alerts = [] 
alert_messages = [] 


def check_price(url):
    headers = {
        "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.87 Safari/537.36'
    }
    try:
        page = requests.get(url, headers=headers)
        soup = BeautifulSoup(page.content, 'html.parser')

       
        price_selectors = [
            '#corePrice_feature_div span.a-price-whole',
            '#priceblock_ourprice',
            '#corePrice_feature_div span.a-price.a-text-price span.a-offscreen'
        ]

        price = None
        for selector in price_selectors:
            price_element = soup.select_one(selector)
            if price_element:
                price = price_element.get_text(strip=True)
                break

        if price:
            price = price.replace(',', '').replace('₹', '').strip()
            return float(price) if price else None
    except Exception as e:
        st.error(f"Error fetching price: {e}")
    return None


def send_email(recipient_email, url, current_price):
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            subject = 'Price Drop Alert'
            body = f'The price for {url} has dropped to ₹{current_price:.2f}!' 
            msg = f'Subject: {subject}\n\n{body}'
            server.sendmail(SENDER_EMAIL, recipient_email, msg.encode('utf-8'))  
            return True
    except Exception as e:
        st.error(f"Error sending email: {e}")
        return False


st.title("Price Wise")
st.subheader("Track prices from retailers and get notified of drops")

url = st.text_input("Enter Product URL", "")
target_price = st.number_input("Enter Target Price", min_value=0.0, step=1.0)
recipient_email = st.text_input("Your Email", "")

if st.button("Set Alert"):
    if url and target_price > 0 and recipient_email:
        current_price = check_price(url)  
        if current_price is not None:
            st.write(f"Current Price when alert was set: ₹{current_price:.2f}")
            alerts.append({'url': url, 'email': recipient_email, 'targetPrice': target_price})
            alert_messages.append(f"Alert set for ₹{target_price} on {url}. Current price: ₹{current_price:.2f}.")
            st.success("Alert has been set!")

            if current_price < target_price:
                alert_messages.append(f"**Immediate Alert:** Current Price: ₹{current_price:.2f} is below your target price of ₹{target_price:.2f}.")
                if send_email(recipient_email, url, current_price):
                    st.success(f"Immediate alert email sent to {recipient_email}!")

        else:
            st.error("Could not fetch the current price. Please check the URL.")

def monitor_alerts():
    while True:
        time.sleep(60)  
        for alert in alerts:
            current_price = check_price(alert['url'])
            if current_price is not None:
                if current_price <= alert['targetPrice']:
                    alert_messages.append(f"**Price Alert:** Current Price: ₹{current_price:.2f}, Target Price: ₹{alert['targetPrice']:.2f}")
                    if send_email(alert['email'], alert['url'], current_price):
                        alerts.remove(alert)  
                        st.success(f"Price drop alert sent to {alert['email']} for {alert['url']}!")
        
        for message in alert_messages:
            st.write(message)

if 'monitor_thread' not in st.session_state:
    st.session_state.monitor_thread = Thread(target=monitor_alerts, daemon=True)
    st.session_state.monitor_thread.start()


