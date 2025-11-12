import time
import threading

def iniciar_monitoramento(callback, pino=20, delay=1):
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pino, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    except (ImportError, RuntimeError):
        print("GPIO não disponível.")
        return

    def loop():
        while True:
            if GPIO.input(pino) == GPIO.LOW:
                callback()
                while GPIO.input(pino) == GPIO.LOW:
                    time.sleep(0.05)
                time.sleep(delay)
            else:
                time.sleep(0.05)

    threading.Thread(target=loop, daemon=True).start()
