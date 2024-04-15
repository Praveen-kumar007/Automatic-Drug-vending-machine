import tkinter as tk
from tkinter import messagebox
import time
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import numpy as np
from pyzbar.pyzbar import decode
import RPi.GPIO as GPIO
import time
import qrcode

# Define medicine costs
medicine_costs = {
    "Balamritam": 10.00,
    "Asava and Arishta": 20.00,
    "Medicine3": 30.00,
    "Medicine4": 40.00,
    # Add more medicines and their costs here
}

# GPIO setup
m1 = 11
m2 = 12
GPIO.setmode(GPIO.BOARD)
GPIO.setup(m1, GPIO.OUT)
GPIO.setup(m2, GPIO.OUT)
mot_p1 = GPIO.PWM(m1, 50)
mot_p2 = GPIO.PWM(m2, 50)

# Initialize variables
num = 1
num1 = 1

# Create a dictionary to store medication information including quantity and cost
medication_dict = {}

# Capture video from the camera
cap = cv2.VideoCapture(0)

while True:
    ret, img = cap.read()
    decoded_objects = decode(img)

    for obj in decoded_objects:
        data = obj.data.decode('utf-8')
        obj_type = obj.type
        a = data

        points = obj.polygon
        if len(points) > 4:
            hull = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
            cv2.polylines(img, [hull], True, (0, 255, 0), 2)

        cv2.putText(img, data, (obj.rect.left, obj.rect.top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        cv2.imwrite('/home/pi/images/' + str(num) + '.jpg', img)
        print('Capture ' + str(num) + ' Successful')
        num = num + 1

    cv2.imshow("QR Code Detection", img)

    if num == 2:
        break

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Decoded data
print(str(a))
decode_data = str(a)

# Split decoded data into medication entries
medication_entries = decode_data.split('\n')
cap.release()
cv2.destroyAllWindows()

# Iterate through the medication entries and initialize quantity to 0
for entry in medication_entries:
    parts = entry.split('-')
    if len(parts) == 2:
        medication_name = parts[0].strip()
        dosage_part = parts[1].strip()

        if dosage_part.startswith("Dosage:"):
            dosage = dosage_part.replace("Dosage:", "").strip()

            # Initialize quantity to 0 for each medicine and set the cost
            medication_dict[medication_name] = {"dosage": dosage, "quantity": 0, "cost": medicine_costs.get(medication_name, 0)}

# Define a list of unavailable medicine names
unavailable_medicines = [medicine_name for medicine_name in medication_dict if medicine_name not in medicine_costs]

# Create a function to delete a medication from the dictionary
def delete_medication():
    selected_medication = medication_listbox.get(tk.ACTIVE)
   
    if selected_medication:
        if selected_medication in medication_dict:
            del medication_dict[selected_medication]
            # Remove the medication from the Listbox as well
            medication_listbox.delete(tk.ACTIVE)
            calculate_total_cost()
            messagebox.showinfo("Info", f"{selected_medication} deleted from the dictionary.")
        else:
            messagebox.showerror("Error", f"{selected_medication} not found in the dictionary.")

# Create a function to handle quantity increment
def increment_quantity(medication_name):
    if medication_name in medication_dict:
        medication_dict[medication_name]["quantity"] += 1
        update_quantity_label(medication_name)

# Create a function to handle quantity decrement
def decrement_quantity(medication_name):
    if medication_name in medication_dict and medication_dict[medication_name]["quantity"] > 0:
        medication_dict[medication_name]["quantity"] -= 1
        update_quantity_label(medication_name)

# Create a function to update the quantity label and calculate the cost
def update_quantity_label(medication_name):
    quantity_label = medication_dict[medication_name]["quantity_label"]
    quantity = medication_dict[medication_name]["quantity"]
    cost = medication_dict[medication_name]["cost"]
    quantity_label.config(text=f"Quantity: {quantity} - Cost: {quantity * cost}")
    calculate_total_cost()

# Create a function to calculate the total cost
def calculate_total_cost():
    total_cost = sum(medication_dict[medication_name]["quantity"] * medication_dict[medication_name]["cost"]
                     for medication_name in medication_dict)
    total_cost_label.config(text=f"Total Cost: {total_cost:.2f}")
    return total_cost

# Create the Tkinter GUI window
root = tk.Tk()
root.title("Medication Management System")
root.geometry("800x600")

# Create a frame to hold the medication list
bill_frame = tk.Frame(root)
bill_frame.pack(pady=20)

# Create and place widgets on the bill frame
medication_listbox = tk.Listbox(bill_frame, width=30, height=10)
medication_listbox.pack(side="left", padx=20)

# Create a frame for buttons and quantity labels
button_frame = tk.Frame(bill_frame)
button_frame.pack(side="left", padx=20)

# Create a label for the medication list
medication_label = tk.Label(bill_frame, text="Medication List")
medication_label.pack(side="top")

# Create buttons for each medication to increment and decrement quantities
for medication_name in medication_dict:
    if medication_name in unavailable_medicines:
        medication_listbox.insert(tk.END, medication_name)
        medication_listbox.itemconfig(tk.END, {'fg': 'red'})
    else:
        medication_listbox.insert(tk.END, medication_name)
        medication_listbox.itemconfig(tk.END, {'fg': 'green'})
# Create buttons and labels for each medication in the Listbox
for medication_name in medication_dict:
    frame = tk.Frame(button_frame)
    frame.pack()

    label = tk.Label(frame, text=medication_name, width=15)
    label.pack(side="left")

    increment_button = tk.Button(frame, text="+", command=lambda name=medication_name: increment_quantity(name))
    increment_button.pack(side="left")

    decrement_button = tk.Button(frame, text="-", command=lambda name=medication_name: decrement_quantity(name))
    decrement_button.pack(side="left")

    quantity_label = tk.Label(frame, text=f"Quantity: {medication_dict[medication_name]['quantity']} - Cost: {0.00}")
    quantity_label.pack(side="left")

    # Store the quantity label in the dictionary for later updates
    medication_dict[medication_name]["quantity_label"] = quantity_label

# Create a button to delete selected medication
delete_button = tk.Button(root, text="Delete Medication", command=delete_medication)
delete_button.pack(pady=10)

# Create a label to display the total cost
total_cost_label = tk.Label(root, text="Total Cost: 0.00")
total_cost_label.pack()

def close_gui():
    upi_payment_link = f"upi://pay?pa=praveenrajeshkumar07@oksbi&pn=Praveenkumar&tn=Total%20Cost&am={calculate_total_cost()}&cu=INR"

    # Generate a QR code for the UPI payment link
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(upi_payment_link)
    qr.make(fit=True)

    # Create a QR code image
    img = qr.make_image(fill_color="black", back_color="white")
    qr_photo = ImageTk.PhotoImage(img)

    qr_label.config(image=qr_photo)
    qr_label.photo = qr_photo
   
proceed_button=tk.Button(root,text='Proceed',command=close_gui)
proceed_button.pack()
qr_label=tk.Label(root)
qr_label.pack()

# Start the Tkinter GUI event loop
root.mainloop()
# Save the QR code image to a file

# Display bill,rotate motors
medicine_names = list(medication_dict.keys())
medicine_costs = {}
unavailable_dict = {}

# Separate the keys based on availability
for key in medicine_names:
    if key in medicine_costs:
        medicine_costs[key] = medicine_dict[key]
    else:
        unavailable_dict[key] = None  # You can set a default value here if needed

print("Available Dictionary:")
print(available_dict)

print("\nUnavailable Dictionary:")
print(unavailable_dict)
print(medicine_names)

time.sleep(15)
for name in medicine_names:
    if name.lower() == 'balamritam':
        while num1 < 4:
            mot_p1.start(2.5)
            mot_p1.ChangeDutyCycle(7.5)
            print('360 degree')
            time.sleep(1)
            num1 = num1 + 1
        num1 = 1
    elif name.lower() == 'asava and arishta':
        while num1 < 4:
            mot_p2.start(2.5)
            mot_p2.ChangeDutyCycle(7.5)
            print('360 degree')
            time.sleep(1)
            num1 = num1 + 1
    else:
        print('not available')

GPIO.cleanup()
