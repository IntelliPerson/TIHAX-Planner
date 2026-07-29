from main import *

if __name__ == '__main__':
    connection_string = "tcp:127.0.0.1:5762"  
    #connection_string = "COM6"  # Windows için
    #baud_rate = 57600
    #vehicle = connect(connection_string ,wait_ready=True)
    vehicle=None
    app = MissionPlannerApp()
    threading.Thread(target=dedicated_server, args=()).start()
    #app.geometry(f"{app.winfo_screenwidth()}x{app.winfo_screenheight()-70}+0+0")
    #app.state("zoomed")

    app.mainloop()