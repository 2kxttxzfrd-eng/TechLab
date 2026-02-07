import streamlit as st
import uuid
from datetime import datetime
import smtplib
import ssl
from email.message import EmailMessage
import os
import json # Added json import
from PIL import Image

# --- Image Conversion Utility ---
def ensure_images_converted():
    """
    Checks for .heic images and converts them to .jpg if the .jpg doesn't exist.
    """
    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()
        
        conversion_map = [
            ("1. Mug Insert Light Grey.heic", "1. Mug Insert Light Grey.jpg"),
            ("2.Mug Insert Dark Grey.heic", "2.Mug Insert Dark Grey.jpg")
        ]
        
        for heic_file, jpg_file in conversion_map:
            if os.path.exists(heic_file) and not os.path.exists(jpg_file):
                try:
                    img = Image.open(heic_file)
                    img.save(jpg_file, "JPEG")
                    print(f"Converted {heic_file} to {jpg_file}")
                except Exception as e:
                    print(f"Error converting {heic_file}: {e}")
            elif not os.path.exists(heic_file) and not os.path.exists(jpg_file):
                 print(f"Source file {heic_file} not found.")

    except ImportError:
        print("pillow-heif not installed. Automatic HEIC conversion disabled.")
    except Exception as e:
        print(f"Image conversion setup error: {e}")

# Run conversion on app startup
ensure_images_converted()

# --- Persistence Helpers ---
PRODUCTS_FILE = "products.json"

def load_products():
    """Load products from a JSON file or return defaults."""
    if os.path.exists(PRODUCTS_FILE):
        try:
            with open(PRODUCTS_FILE, "r") as f:
                data = json.load(f)
                # Convert keys back to integers (JSON keys are always strings)
                return {int(k): v for k, v in data.items()}
        except Exception as e:
            print(f"Error loading products: {e}")
    
    # Default Initial Inventory (if file doesn't exist)
    return {
        1: {
            "name": "Mug Insert - Light Grey",
            "price": 10.00,
            "image": "1. Mug Insert Light Grey.jpg",
            "description": "Hey! Is your favorite mug too big for your car’s cup holder? This light grey mug insert is the perfect solution—designed to hold mugs up to 3.5 inches in diameter so you can take your favorite drink on the road. Mug not included.",
            "stock": 5,
            "sold": 1
        },
        2: {
            "name": "Mug Insert - Dark Grey",
            "price": 10.00,
            "image": "2.Mug Insert Dark Grey.jpg",
            "description": "Hey! Is your favorite mug too big for your car’s cup holder? This dark grey mug insert is the perfect solution—designed to hold mugs up to 3.5 inches in diameter so you can take your favorite drink on the road. Mug not included.",
            "stock": 5,
            "sold": 1
        },
        3: {
            "name": "Art Brush Holder",
            "price": 20.00,
            "image": "3.BrushHolder.jpeg",
            "description": "Keep your artistic brushes neat and accessible.",
            "stock": 5,
            "sold": 0
        }
    }

def save_products(products):
    """Save current products state to JSON file."""
    try:
        with open(PRODUCTS_FILE, "w") as f:
            json.dump(products, f, indent=4)
    except Exception as e:
        print(f"Error saving products: {e}")

# --- Configuration & State Initialization ---
def init_state():
    if "products" not in st.session_state:
        # Load from file instead of hardcoding
        st.session_state.products = load_products()
    
    if "cart" not in st.session_state:
        st.session_state.cart = {}  # {product_id: quantity}

    if "orders" not in st.session_state:
        st.session_state.orders = []

# --- Helper Functions ---
def add_to_cart(product_id):
    if product_id in st.session_state.cart:
        st.session_state.cart[product_id] += 1
    else:
        st.session_state.cart[product_id] = 1
    st.success("Added to cart!")

def get_product(p_id):
    return st.session_state.products.get(p_id)

def send_order_emails(order):
    """
    Sends order confirmation to the Customer and a notification to the Owner.
    """
    # --- EMAIL CONFIGURATION (Update this section!) ---
    formatted_sender_email = "TechLabbyTyler@gmail.com"  # e.g., techlab.orders@gmail.com
    sender_password = "uaej tqjm ggve gdsm"          # App Password (not login password)
    owner_email = "TechLabbyTyler@gmail.com"          # Your personal email

    if "your_" in formatted_sender_email:
        print("Email config incomplete. Skipping emails.")
        return

    # 1. Prepare Content (Shared)
    items_text = ""
    for p_id, qty in order['items'].items():
        if p_id in st.session_state.products:
            p_name = st.session_state.products[p_id]['name']
            items_text += f"- {p_name} (x{qty})\n"
        else:
            items_text += f"- Product ID {p_id} (x{qty})\n"

    # 2. Email to CUSTOMER
    msg_customer = EmailMessage()
    msg_customer['Subject'] = f"Order Confirmation: {order['id']} - TechLab"
    msg_customer['From'] = formatted_sender_email
    msg_customer['To'] = order['email']
    msg_customer.set_content(f"""
Hi {order['customer']},

Thank you for your order! Here are your order details:

Order ID: {order['id']}
Total: ${order['total']:.2f}

Items Ordered:
{items_text}

--- NEXT STEPS ---
1. PAYMENT: Please Venmo ${order['total']:.2f} to @TechLab-Parent.
   * IMPORTANT: Include Order ID {order['id']} in the Venmo note.

2. PICKUP: Once payment is received, I will start printing. We will arrange a local pickup time when it's ready.

Any questions? Reply to this email!

Thanks,
Tyler's TechLab 🖨️
    """)

    # 3. Email to OWNER
    msg_owner = EmailMessage()
    msg_owner['Subject'] = f"NEW ORDER: {order['id']} (${order['total']:.2f})"
    msg_owner['From'] = formatted_sender_email
    msg_owner['To'] = owner_email
    msg_owner.set_content(f"""
New Order Received!

Customer: {order['customer']}
Email: {order['email']}
Note: {order['note']}

Items:
{items_text}

Total: ${order['total']:.2f}
    """)

    # 4. Send Emails
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(formatted_sender_email, sender_password)
            
            # Send to Customer
            smtp.send_message(msg_customer)
            # Send to Owner
            smtp.send_message(msg_owner)
            
        print(f"Emails sent successfully for Order {order['id']}")
    except Exception as e:
        print(f"Error sending emails: {e}")

# --- Page Functions ---

def show_home():
    st.title("Welcome to Tyler's TechLab 🖨️")
    st.write("### Cool 3D Printed Gear by a Teen Maker")
    
    # --- Merged About Section ---
    st.markdown("""
    Hi! I'm a 15-year-old maker passionate about 3D printing and design. 
    TechLab is my small business where I share my useful and fun creations with the community.
    Everything is printed locally on my 3D printer. Thanks for supporting young makers!
    """)
    st.markdown("---")
    # ----------------------------

    st.write("Browse our latest creations below. All items are printed on demand.")

    products = st.session_state.products
    
    # Display products in columns (Updated to 3 columns for smaller images on wide layout)
    cols = st.columns(3)
    
    for idx, (p_id, p_data) in enumerate(products.items()):
        col = cols[idx % 3]
        with col:
            try:
                st.image(p_data["image"], use_container_width=True)
            except Exception:
                st.error(f"Image not found: {p_data['image']}")
            
            st.subheader(p_data["name"])
            st.write(p_data["description"])
            st.write(f"**Price:** ${p_data['price']:.2f}")
            
            # Inventory Display
            st.caption(f"Stock: {p_data['stock']} | Sold: {p_data['sold']}")
            
            if st.button(f"Add to Order", key=f"add_{p_id}"):
                add_to_cart(p_id)

def show_cart_page():
    st.title("Your Order")
    
    if not st.session_state.cart:
        st.info("Your cart is empty. Go to Home to add items.")
        return

    total_price = 0
    st.write("### Items in your cart:")
    
    # Display Cart Items
    for p_id, qty in st.session_state.cart.items():
        product = get_product(p_id)
        if product:
            subtotal = product["price"] * qty
            total_price += subtotal
            st.write(f"**{product['name']}** (x{qty}) - ${subtotal:.2f}")

    st.markdown("---")
    st.subheader(f"Total: ${total_price:.2f}")

    st.write("### Checkout Details")
    st.info("I do not collect payments directly on this site.")
    
    with st.form("checkout_form"):
        customer_name = st.text_input("Your Name")
        parent_email = st.text_input("Parent/Guardian Email (required)")
        note = st.text_area("Order Notes (optional)")
        
        submitted = st.form_submit_button("Place Order")
        
        if submitted:
            if not parent_email:
                st.error("Please enter a parent/guardian email.")
            else:
                # Process Order
                process_order(customer_name, parent_email, note, total_price)

def process_order(name, email, note, total):
    # Generate Order ID
    order_id = str(uuid.uuid4())[:8].upper()
    
    # Update Inventory (Simple decrement logic based on 'sold' metric)
    for p_id, qty in st.session_state.cart.items():
        if p_id in st.session_state.products:
            st.session_state.products[p_id]['sold'] += qty
            # Optionally decrease stock if that's the logic intended, 
            # but request said track stock vs. sold.
            st.session_state.products[p_id]['stock'] -= qty

    # Save updated inventory to file
    save_products(st.session_state.products)

    # Save Order
    new_order = {
        "id": order_id,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "customer": name,
        "email": email,
        "items": st.session_state.cart.copy(),
        "total": total,
        "note": note
    }
    st.session_state.orders.append(new_order)
    
    # Send Emails (Owner + Customer)
    send_order_emails(new_order)
    
    # Clear Cart
    st.session_state.cart = {}
    
    # Success Message & Instructions
    st.balloons()
    st.success(f"Order Placed! Your Order ID is: **{order_id}**")
    
    st.markdown("""
    ### Next Steps
    1. **Payment**: Please Venmo the total amount to the QR code below.
       * Include your Order ID in the payment note.
    """)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        if os.path.exists("Venmo.jpg"):
            st.image("Venmo.jpg", caption="Scan to Pay", use_container_width=True)
            
    st.markdown("""
    2. **Production**: Once payment is received, I will start printing your order (this may take a few days).
    3. **Pickup**: We will arrange a local pick up time when your order is ready.
    
    _A confirmation email will be sent to the address provided._
    """)

def show_contact():
    st.title("Contact")
    st.write("Have a question? Custom request?")
    st.write("Email me at: **TechLabbyTyler@gmail.com**")

# --- Main App Execution ---

def main():
    st.set_page_config(page_title="TechLab", page_icon="🖨️", layout="wide")
    init_state()
    
    # Sidebar Navigation
    st.sidebar.title("Navigation")
    # Products removed from nav as per request, merged into Home
    # "About" removed from nav as per request, merged into Home
    page = st.sidebar.radio("Go to", ["Home", "Your Order", "Contact"])
    
    # Cart Summary in Sidebar
    cart_count = sum(st.session_state.cart.values())
    if cart_count > 0:
        st.sidebar.info(f"🛒 In Cart: {cart_count} items")

    if page == "Home":
        show_home()
    elif page == "Your Order":
        show_cart_page()
    elif page == "Contact":
        show_contact()

if __name__ == "__main__":
    main()