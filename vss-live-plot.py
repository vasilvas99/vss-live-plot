#!/usr/bin/env python3

import argparse
import os
from collections import deque
from time import monotonic
from urllib.parse import urlparse

import matplotlib.animation as animation
import matplotlib.pyplot as plt
from kuksa_client.grpc import VSSClient


def read_datapoint(datapoint_path, databroker_host, databroker_port):
    with VSSClient(databroker_host, databroker_port) as kuksa_client:
        kuksa_response = kuksa_client.get_current_values([datapoint_path])

    if kuksa_response[datapoint_path]:
        return kuksa_response[datapoint_path].value
    else:
        return 0


# This function is called periodically from FuncAnimation
def draw_plot_frame(
    i,
    ax,
    ts,
    ys,
    datapoint_path,
    databroker_host,
    databroker_port,
    initial_time=0,
):
    datapoint_val = read_datapoint(datapoint_path, databroker_host, databroker_port)

    ts.append(monotonic() - initial_time)
    ys.append(datapoint_val)

    # Draw t and y lists
    ax.clear()
    ax.plot(ts, ys)

    # Format plot
    plt.title(f"Live plot of {datapoint_path}")
    plt.ylabel("Datapoint Value")
    plt.xlabel("Time (s)")


def cli(cli_args=None):
    parser = argparse.ArgumentParser(
        description="Live plots a single datapoint in the Kuksa databroker for monitoring purposes"
    )
    parser.add_argument(
        "VSS_PATH", type=str, help="VSS Datapoint to be plotted/monitored"
    )
    parser.add_argument(
        "-d",
        "--databroker-address",
        type=str,
        default="127.0.0.1:55555",
        help="The address to the kuksa databroker. [DEFAULT: 127.0.0.1:55555]",
    )
    parser.add_argument(
        "-u",
        "--plot-update-ms",
        type=int,
        default=200,
        help="Interval at which the plot is updated (ms) [DEFAULT: 200]",
    )
    parser.add_argument(
        "-q",
        "--plot-queue-length",
        type=int,
        default=200,
        help="Number of points plotted at a time (history length) [DEFAULT: 200]",
    )
    return parser.parse_args(cli_args)


def main(cli_args=None):
    conf = cli(cli_args)
    databroker_url = urlparse(f"//{conf.databroker_address}/")
    initial_time = monotonic()

    # Create figure for plotting
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ts = deque(maxlen=conf.plot_queue_length)
    ys = deque(maxlen=conf.plot_queue_length)

    # Setup the function that generates frames
    ani = animation.FuncAnimation(
        fig,
        draw_plot_frame,
        fargs=(
            ax,
            ts,
            ys,
            conf.VSS_PATH,
            databroker_url.hostname,
            databroker_url.port,
            initial_time,
        ),
        interval=conf.plot_update_ms,
        cache_frame_data=False,
    )
    plt.show()


if __name__ == "__main__":
    main()
