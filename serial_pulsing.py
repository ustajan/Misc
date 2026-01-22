"""
Generate active-high pulses on the TX line of a serial adapter.

Usage:
    python serial_pulsing.py --port /dev/tty.usbserial-XXXX --pulse-us 5000 --period-us 20000 --count 100

Inputs for pulse and period are in microseconds (us).

This inverts the original behavior: the line is held idle-low between pulses,
and released (idle-high) for the pulse width. Uses ser.break_condition when
available; falls back to ser.send_break if supported by the backend.
"""
import time
import argparse
import serial

def pulse_tx(port, baud=115200, pulse_us=5000.0, period_us=20000.0, count=100, timeout=1.0):
    # ensure period > pulse
    pulse_us = float(pulse_us)
    period_us = float(period_us)
    if period_us <= pulse_us:
        period_us = pulse_us + 1.0
    sleep_rem_us = period_us - pulse_us

    try:
        ser = serial.Serial(port, baudrate=baud, timeout=timeout)
    except Exception as e:
        raise SystemExit(f"Failed to open {port}: {e}")

    try:
        # Prefer persistent break control (set True => TX low). We'll hold TX low
        # between pulses and release it briefly for the active-high pulse.
        if hasattr(ser, "break_condition"):
            print(f"Using break_condition to generate active-high pulses on {port}")
            # set idle-low
            ser.break_condition = True
            try:
                for i in range(int(count)):
                    # pulse: release break => TX returns high
                    ser.break_condition = False
                    time.sleep(pulse_us / 1e6)
                    # return to idle-low
                    ser.break_condition = True
                    if sleep_rem_us > 0:
                        time.sleep(sleep_rem_us / 1e6)
            finally:
                # ensure we release break on exit (leave line idle-high)
                ser.break_condition = False

        # Fallback: use send_break to generate the idle-low intervals (blocking)
        elif hasattr(ser, "send_break"):
            for i in range(int(count)):
                # drive TX low for the idle interval (sleep_rem_us)
                if sleep_rem_us > 0:
                    try:
                        ser.send_break(duration=sleep_rem_us / 1e6)
                    except TypeError:
                        # some backends accept no duration argument
                        ser.send_break()
                        time.sleep(sleep_rem_us / 1e6)
                # after send_break returns, line is high => active pulse
                time.sleep(pulse_us / 1e6)

        else:
            raise RuntimeError("Serial backend does not support break_condition or send_break; cannot produce active-high pulses.")
    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        ser.close()

def main():
    p = argparse.ArgumentParser(description="Generate active-high pulses on serial TX line using break condition. Inputs in microseconds (us).")
    p.add_argument("--port", "-p", required=True, help="Serial device (e.g. /dev/tty.usbserial-XXXX)")
    p.add_argument("--baud", "-b", type=int, default=115200, help="Baud rate (unused for break but required to open port)")
    p.add_argument("--pulse-us", type=float, default=5000.0, help="Pulse width in microseconds (TX high duration)")
    p.add_argument("--period-us", type=float, default=20000.0, help="Period in microseconds")
    p.add_argument("--count", "-n", type=int, default=100, help="Number of pulses (use 0 for continuous)")
    args = p.parse_args()

    if args.count == 0:
        try:
            while True:
                pulse_tx(args.port, baud=args.baud, pulse_us=args.pulse_us, period_us=args.period_us, count=1000)
        except KeyboardInterrupt:
            print("Stopped.")
    else:
        pulse_tx(args.port, baud=args.baud, pulse_us=args.pulse_us, period_us=args.period_us, count=args.count)

if __name__ == "__main__":
    main()