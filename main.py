import serial
import time
import serial.tools.list_ports #u gotta do pip install pyserial
import threading
from discord_webhook import DiscordWebhook, DiscordEmbed
from datetime import datetime
import pyperclip



# Define the AT command to check for new messages
AT_COMMAND_TEXT_MODE = "AT+CMGF=1"
AT_COMMAND_CHECK_MESSAGES = "AT+CMGL=\"REC UNREAD\""
AT_COMMAND_CHECK_SELF = "AT+CNUM"


# Function to send an AT command and receive the response
def send_at_command(port, command):
    port.write(command.encode() + b"\r")
    time.sleep(1.5)
    response = port.read_all().decode()
    return response

def check_for_sms (port_name, index,numbers):
    with open('webhook', 'r') as file:
        webhook = file.readline().strip()
    # Start an infinite loop to continuously check for new messages
    while True:
        try:
            # Establish connection to the COM port
            port = serial.Serial(port_name, 115200, timeout=1)
            # Send AT command to enable Text Mode
            response = send_at_command(port, AT_COMMAND_TEXT_MODE)
            # Send AT command to retrieve unread messages
            response = send_at_command(port, AT_COMMAND_CHECK_MESSAGES)

            # > 30 was a simple way to detect a message had arrived
            if len(response) > 30:
                response = response[response.rfind('"')+1:response.rfind("OK")]
                print(response)
                # Copies the code received to clipboard
                pyperclip.copy(response[2:8])
                webhook = DiscordWebhook(url=webhook)
                embed = DiscordEmbed(
                    title=numbers[index] + " @ " + port_name + " Received A Text", description=response, color='03b2f8'
                )

                embed.set_footer(text=datetime.now().strftime("%I:%M %p"))
                print(f"New Message Detected at {port_name}!")
                webhook.add_embed(embed)
                response1 = webhook.execute()

            port.close()
        except serial.SerialException as e:
            print(f"Error connecting to {port_name}: {str(e)}")
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        # Delay between consecutive checks
        time.sleep(1)

# For testing ports manually
#check_for_sms("COM8",1,0)

# Get a list of all active COM ports
com_ports = [port.device for port in serial.tools.list_ports.comports()]
numbers = []
for port_name in com_ports:
   try:
       # Establish connection to the COM port
       port = serial.Serial(port_name, 115200, timeout=1)
       print(f"Connected to {port_name}.")
       # Send AT command to check own phone number
       response = send_at_command(port, AT_COMMAND_CHECK_SELF)
       start = '","'
       end = '",145'
       numbers.append(response[response.find(start)+len(start):response.rfind(end)])
       port.close()
       print(f"Disconnected from {port_name}.")
   except Exception as e:
       print(f"Error connecting to {port_name}: {str(e)}")
   except Exception as e:
       print(f"An error occurred: {str(e)}")



# Create and start multiple threads using a loop
threads = []
for i in range(len(com_ports)):
    t = threading.Thread(target=check_for_sms, args=(com_ports[i],i,numbers))
    threads.append(t)
    t.start()