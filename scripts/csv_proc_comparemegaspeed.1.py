import numpy as np
import matplotlib.pyplot as plt
import sys

ms_pixelCal = 13.94736842
ms_timeCal = 300.


def main():

    ms1_path = sys.argv[1]
    ms2_path = sys.argv[2]
    name = sys.argv[3]

    print()
    print(ms1_path)
    print()
    print(ms2_path)
    print()

    ### MegaSpeed 1
    ms1_areas = []
    ms1_velocities = []
    with open(ms1_path) as f:
        for line in f:
            l = line.split(",")
            area = float(l[2])
            vel = float(l[3])
            ms1_areas.append(area)
            ms1_velocities.append(vel)

    ms1_areas = np.array(ms1_areas)
    ms1_velocities = np.array(ms1_velocities)
    ms1_diameters = (2.0 * np.sqrt(ms1_areas / np.pi)) * ms_pixelCal
    ms1_velocities = -ms1_velocities * ms_pixelCal * ms_timeCal / 1e6

    ### MegaSpeed 2
    ms2_areas = []
    ms2_velocities = []
    with open(ms2_path) as f:
        for line in f:
            l = line.split(",")
            area = float(l[2])
            vel = float(l[3])
            ms2_areas.append(area)
            ms2_velocities.append(vel)

    ms2_areas = np.array(ms2_areas)
    ms2_velocities = np.array(ms2_velocities)
    ms2_diameters = (2.0 * np.sqrt(ms2_areas / np.pi)) * ms_pixelCal * 4
    ms2_velocities = -ms2_velocities * ms_pixelCal * 2 * ms_timeCal / 1e6

    ###  ----   Plot Diameter
    filt = inlier_range

    my_dpi = 192
    plt.figure(figsize=(2800 / my_dpi, 1600 / my_dpi), dpi=my_dpi)
    # plot_boxes = 30  # 100

    # Plot filtering
    ms1_diameter_lo, ms1_diameter_hi = filt(ms1_diameters)
    ms1_diameters_filtered = ms1_diameters[
        (ms1_diameters > ms1_diameter_lo) & (ms1_diameters < ms1_diameter_hi)
    ]
    print(
        "Megaspeed 1 diameter filter range", str(ms1_diameter_lo), str(ms1_diameter_hi)
    )

    ms2_diameter_lo, ms2_diameter_hi = filt(ms2_diameters)
    ms2_diameters_filtered = ms2_diameters[
        (ms2_diameters > ms2_diameter_lo) & (ms2_diameters < ms2_diameter_hi)
    ]
    print(
        "Megaspeed 2 diameter filter range", str(ms2_diameter_lo), str(ms2_diameter_hi)
    )

    # Plot range calculations
    plot_low = min(ms2_diameter_lo, ms1_diameter_lo)
    plot_high = max(ms2_diameter_hi, ms1_diameter_hi)

    plot_range = plot_high - plot_low

    plot_low -= 0.05 * plot_range
    plot_high += 0.05 * plot_range

    # Number of bins
    bin_size = FreedmanDiaconis(list(ms1_diameters) + list(ms2_diameters))
    plot_boxes = int(plot_range / bin_size)

    # Generate plots
    plt.subplot(211)
    plt.title("MegaSpeed Blur Diameters n=" + str(len(ms1_diameters_filtered)))
    plt.hist(ms1_diameters_filtered, plot_boxes, (plot_low, plot_high))
    plt.xlabel("Diameter (microns)")

    plt.subplot(212)
    plt.title("Megaspeed Deblur Diameters n=" + str(len(ms2_diameters_filtered)))
    plt.hist(ms2_diameters_filtered, plot_boxes, (plot_low, plot_high))
    plt.xlabel("Diameter (microns)")

    plt.suptitle(name, fontsize="xx-large")
    plt.subplots_adjust(hspace=0.5)
    # plt.savefig(
    #     "/home/mot/tmp/kev_tmp/" + name.replace(" ", "_") + "_diameters.png", dpi=my_dpi
    # )
    # CHANGE folder location
    plt.waitforbuttonpress(0)
    plt.close("all")

    # End diameter plot


def FreedmanDiaconis(d):
    lo, hi = full_range(d)
    bin_size = 2 * iqr(d) / np.cbrt(len(d))
    return bin_size


def iqr(d):
    q75, q25 = np.percentile(d, [75, 25])
    return q75 - q25


def inlier_range(d):
    q75, q25 = np.percentile(d, [75, 25])
    iqr = q75 - q25
    return (q25 - (iqr * 1.5), q75 + (iqr * 1.5))


def full_range(d):
    return np.min(d), np.max(d)


if __name__ == "__main__":
    main()
