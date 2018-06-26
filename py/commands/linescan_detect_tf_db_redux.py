
from lib.Linescan import Linescan2
import numpy as np
import time
import os
from pathlib import Path

import config

from skimage import data, io, filters
from scipy.ndimage.morphology import (
    binary_dilation,
    binary_erosion,
    grey_dilation,
    grey_erosion,
)
from skimage.morphology import watershed, diamond
from skimage.segmentation import random_walker
from scipy.ndimage.measurements import watershed_ift
from skimage.feature import peak_local_max
from skimage import measure

from scipy import ndimage


from scipy.misc import imresize
from dateutil.parser import parse as dateparse

import cv2

from uuid import uuid4
import shutil
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import math


from lib.Database import Database, DBWriter


"""
Note: currently modified to dump results to csv
"""


async def main(args):

    if len(args) < 2:
        print(
            """path/to/linescan/data/ 2018-05-22 Name-of_experiment "Notes. Notes." """
        )
    else:
        print(await detect_linescan(*args))


class LS_Stats:

    def __init__(self, number_of_frames, number_of_particles):
        self.count = 0
        self.number_of_frames = number_of_frames
        self.number_of_particles = number_of_particles
        self.particle_counts = np.zeros(self.number_of_frames)
        self.areas_filled = np.zeros(self.number_of_particles)
        self.areas_by_diameter = np.zeros(self.number_of_particles)
        self.diameters = np.zeros(self.number_of_particles)
        self.radius = np.zeros(self.number_of_particles)
        self.orientations = np.zeros(self.number_of_particles)
        self.eccentricities = np.zeros(self.number_of_particles)
        self.solidities = np.zeros(self.number_of_particles)
        self.velocities = np.zeros(self.number_of_particles)

    def add(self, frame, particle):
        LS_pixelCal = 7.797271
        LS_pixelCal2 = LS_pixelCal ** 2
        LS_timeCal = 4000.

        bb = particle.bbox
        h, w = bb[2] - bb[0], bb[3] - bb[1]

        self.particle_counts[frame] += 1
        self.areas_filled[self.count] = (
            particle.filled_area * LS_pixelCal2
            + np.random.uniform(-LS_pixelCal2 / 2., LS_pixelCal2 / 2.)
        )

        d = (particle.major_axis_length * particle.minor_axis_length) / np.sqrt(
            (particle.minor_axis_length * np.cos(particle.orientation)) ** 2
            + (particle.major_axis_length * np.sin(particle.orientation)) ** 2
        ) * LS_pixelCal + np.random.uniform(-LS_pixelCal / 2., LS_pixelCal / 2.)

        v = (
            (
                LS_timeCal
                * (
                    d
                    / (
                        h * LS_pixelCal
                        + np.random.uniform(-LS_pixelCal / 2., LS_pixelCal / 2.)
                    )
                )
                + np.random.uniform(-LS_timeCal / 2., LS_timeCal / 2.)
            )
            * LS_pixelCal
            + np.random.uniform(-LS_pixelCal / 2., LS_pixelCal / 2.)
        ) / 1000000.0

        a = ((d / 2.0) ** 2) * np.pi

        self.areas_by_diameter[self.count] = a
        self.diameters[self.count] = d
        self.radius[self.count] = d / 2.0
        self.orientations[self.count] = particle.orientation
        self.eccentricities[self.count] = particle.eccentricity
        self.solidities[self.count] = particle.solidity
        self.velocities[self.count] = v

        self.count += 1

        return d, v, a


# date, name = "Unknown", notes = "",
async def detect_linescan(path, date, name, notes="", *args):

    LS_pixelCal = 7.797271
    LS_timeCal = 4000.

    # set up path related stuff

    if not os.path.isdir(path):
        raise ValueError("Directory {} not found".format(path))
    else:
        path = Path(path)

    experiment_uuid = uuid4()
    print("Experiment", experiment_uuid)

    experiment_dir = Path(os.path.join(config.experiment_dir, str(experiment_uuid)))

    if not os.path.isdir(experiment_dir):
        try:
            os.makedirs(experiment_dir)
        except:
            raise ValueError(
                "Experiment directory {} could not be created".format(dump_path)
            )

    # Load linescan data

    ls = Linescan2(path, debug=False)

    print("loaded")

    start = time.time()

    sy, ey, sx, ex = 150000, 155000, 0, 4000

    db = Database()
    tx, transaction = await db.transaction()

    try:

        print("Saving representitive images.")

        im = ls.im[sy:ey, sx:ex]
        dv = ls.dv[sy:ey, sx:ex]
        mk = ls.mk[sy:ey, sx:ex]

        io.imsave(experiment_dir / "image.jpg", im, "pil")
        io.imsave(experiment_dir / "divided.jpg", dv, "pil")
        io.imsave(experiment_dir / "mask.jpg", mk, "pil")

        # Calculate summary statistics (pass 1)
        print("Collecting statistics")

        number_of_frames = math.ceil(len(ls.im) / 1000)

        stats = LS_Stats(number_of_frames, len(ls.props))

        frame_uuids = [
            {"added": False, "uuid": uuid4()} for i in range(number_of_frames)
        ]

        with open(experiment_dir / "detections.csv", "w") as detections:

            detections.write(
                "Frame ID, Particle ID, Area, Velocity, Intensity, Perimeter, X Position, Y Position, Major Axis, Minor Axis, Orientation, Solidity, Eccentricity, Diameter, Width, Height\n"
            )

            print("Writing out", experiment_dir / "detections.csv")

            await tx.execute(
                "INSERT INTO Experiment (experiment, day, name, method, notes) VALUES ($1, $2, $3, $4, $5)",
                str(experiment_uuid),
                dateparse(date),
                name,
                "linescan",
                notes,
            )

            for p in ls.props:

                bb = p.bbox
                h, w = bb[2] - bb[0], bb[3] - bb[1]

                if w >= 5.0:

                    particle_uuid = uuid4()
                    frame = math.floor(bb[0] / 1000.)
                    frame_uuid = frame_uuids[frame]

                    d, v, a = stats.add(frame, p)

                    # Small note: for linescan data, segment_uuid == frame_uuid
                    # and track_uuid == particle_uuid

                    if not frame_uuid["added"]:
                        print("Saving frame", frame)
                        await tx.execute(
                            "INSERT INTO Segment (segment, experiment, number) VALUES ($1, $2, $3)",
                            str(frame_uuid["uuid"]),
                            str(experiment_uuid),
                            frame,
                        )
                        await tx.execute(
                            "INSERT INTO Frame (frame, experiment, segment, number) VALUES ($1, $2, $3, $4)",
                            str(frame_uuid["uuid"]),
                            str(experiment_uuid),
                            str(frame_uuid["uuid"]),
                            frame,
                        )
                        frame_uuids[frame]["added"] = True

                    if not os.path.isdir(experiment_dir / str(frame_uuid["uuid"])):
                        os.makedirs(experiment_dir / str(frame_uuid["uuid"]))

                    io.imsave(
                        experiment_dir
                        / str(frame_uuid["uuid"])
                        / "{}.jpg".format(particle_uuid),
                        collage_crops(ls, p),
                        "pil",
                    )

                    # Frame Number, Frame ID, Particle ID, Area,           Velocity, Intensity,        Perimeter,   X Position,    Y Position,    Major Axis,          Minor Axis,          Orientation,   Solidity,   Eccentricity,   Diameter, Width, Height.
                    csv_attrs = [
                        frame,
                        frame_uuid,
                        particle_uuid,
                        a,
                        v,
                        p.mean_intensity,
                        p.perimeter,
                        p.centroid[1],
                        p.centroid[0],
                        p.major_axis_length,
                        p.minor_axis_length,
                        p.orientation,
                        p.solidity,
                        p.eccentricity,
                        d,
                        w,
                        h,
                    ]

                    csv_line = ",".join(list(map(str, csv_attrs))) + "\n"

                    detections.write(csv_line)

                    await tx.execute(
                        "INSERT INTO Particle (particle, experiment, area, intensity, perimeter, radius, category, major, minor, orientation, solidity, eccentricity) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)",
                        str(particle_uuid),
                        str(experiment_uuid),
                        a,
                        p.mean_intensity,
                        p.perimeter,
                        d / 2.0,
                        0,
                        p.major_axis_length,
                        p.minor_axis_length,
                        p.orientation,
                        p.solidity,
                        p.eccentricity,
                    )

                    await tx.execute(
                        "INSERT INTO Track (track, frame, particle, location, bbox) VALUES ($1, $2, $3, $4, $5)",
                        str(particle_uuid),
                        str(frame_uuid["uuid"]),
                        str(particle_uuid),
                        (p.centroid[1], p.centroid[0]),
                        ((p.bbox[1], p.bbox[0]), (p.bbox[3], p.bbox[2])),
                    )

        print("Rendering summary plots")

        filter_area_min = 1
        filter_area_max = 999999999999

        # areas_filled
        # areas_by_diameter

        mask = (stats.areas_filled > filter_area_min) & (
            stats.areas_filled < filter_area_max
        )
        n_str = str(np.count_nonzero(mask))

        print("Statictics collected")

        # Generate some summary charts

        figsize, dpi = (7, 5), 300

        areasp_fig, areasp_ax1 = plt.subplots(
            figsize=figsize, dpi=dpi, tight_layout=True
        )
        areasp_ax1.set_title(f"Areas (filled) n={n_str}")
        areasp_ax1.hist(stats.areas_filled[mask], 50, (0, 25e4))
        areasp_ax1.set_yscale("log")
        areasp_ax1.set_xlabel("Area (microns)")
        areasp_fig.savefig(experiment_dir / "area-filled-histogram.png")

        areasc_fig, areasc_ax1 = plt.subplots(
            figsize=figsize, dpi=dpi, tight_layout=True
        )
        areasc_ax1.set_title(f"Areas (by diameter) n={n_str}")
        areasc_ax1.hist(stats.areas_by_diameter[mask], 50, (0, 25e4))
        areasc_ax1.set_xlabel("Area (microns)")
        areasc_ax1.set_yscale("log")
        areasc_fig.savefig(experiment_dir / "area-dia-histogram.png")

        eccen_fig, eccen_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
        eccen_ax1.set_title(f"Eccentricities n={n_str}")
        eccen_ax1.set_xlabel("Eccentricity")
        eccen_ax1.hist(stats.eccentricities[mask], 50, (0, 1))
        eccen_fig.savefig(experiment_dir / "eccentricities-histogram.png")

        orien_fig, orien_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
        orien_ax1.set_title(f"Orientations n={n_str}")
        orien_ax1.set_xlabel("Orientation (radians)")
        orien_ax1.hist(stats.orientations[mask], 135, (-(np.pi / 2), +(np.pi / 2)))
        orien_fig.savefig(experiment_dir / "orientation-histogram.png")

        veloc_fig, veloc_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
        veloc_ax1.set_title(f"Velocities n={n_str}")
        veloc_ax1.set_xlabel("Velocity (m/s)")
        veloc_ax1.hist(stats.velocities[mask], 50, (0, 0.1))
        veloc_fig.savefig(experiment_dir / "velocity-histogram.png")

        dia_fig, dia_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
        dia_ax1.set_title(f"Diameters n={n_str}")
        dia_ax1.set_xlabel("Diameter (microns)")
        dia_ax1.hist(stats.diameters[mask], 50, (0, 700))
        dia_fig.savefig(experiment_dir / "diameter-histogram.png")

        solid_fig, solid_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
        solid_ax1.set_title(f"Solidities n={n_str}")
        solid_ax1.set_yscale("log")
        solid_ax1.set_xlabel("Solidities")
        solid_ax1.hist(stats.solidities[mask], 50, (0, 1))
        solid_fig.savefig(experiment_dir / "solidity-histogram.png")

        count_fig, count_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
        count_ax1.set_title(f"Particle Counts / Frame n={n_str}")
        count_ax1.set_xlabel("Frame #")
        count_ax1.plot(stats.particle_counts)
        count_fig.savefig(experiment_dir / "particle-counts.png")

        th_fig, th_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
        th_ax1.set_title(f"Thresholds n={n_str}")
        th_ax1.set_xlabel("Frame #")
        th_ax1.plot(ls.th)
        th_fig.savefig(experiment_dir / "threshold.png")

        Ap_x_V_fig, Ap_x_V_ax1 = plt.subplots(
            figsize=figsize, dpi=dpi, tight_layout=True
        )
        Ap_x_V_ax1.set_title(f"Area (filled) / Velocites n={n_str}")
        Ap_x_V_ax1.set_xlabel("Area (microns)")
        Ap_x_V_ax1.hist2d(
            stats.areas_filled[mask],
            stats.velocities[mask],
            150,
            ((0, 25e4), (0, 0.1)),
            norm=colors.LogNorm(),
        )
        Ap_x_V_fig.savefig(experiment_dir / "area-filled_x_velocity-histogram.png")

        Ac_x_V_fig, Ac_x_V_ax1 = plt.subplots(
            figsize=figsize, dpi=dpi, tight_layout=True
        )
        Ac_x_V_ax1.set_title(f"Area (by diameter) / Velocites n={n_str}")
        Ac_x_V_ax1.set_xlabel("Area (microns)")
        Ac_x_V_ax1.hist2d(
            stats.areas_by_diameter[mask],
            stats.velocities[mask],
            150,
            ((0, 25e4), (0, 0.1)),
            norm=colors.LogNorm(),
        )
        Ac_x_V_fig.savefig(experiment_dir / "area-dia_x_velocity-histogram.png")

        D_x_V_fig, D_x_V_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
        D_x_V_ax1.set_title(f"Diameter / Velocites n={n_str}")
        D_x_V_ax1.set_xlabel("Diameter (microns)")
        D_x_V_ax1.hist2d(
            stats.diameters[mask],
            stats.velocities[mask],
            150,
            ((0, 700), (0, 0.1)),
            norm=colors.LogNorm(),
        )
        D_x_V_fig.savefig(experiment_dir / "diameter_x_velocity-histogram.png")

        O_x_V_fig, O_x_V_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
        O_x_V_ax1.set_title(f"Orientation / Velocites n={n_str}")
        O_x_V_ax1.set_xlabel("Orientation (radians)")
        O_x_V_ax1.hist2d(
            stats.orientations[mask],
            stats.velocities[mask],
            150,
            ((-1.8, 1.8), (0, 0.1)),
            norm=colors.LogNorm(),
        )
        O_x_V_fig.savefig(experiment_dir / "orientation_x_velocity-histogram.png")

        E_x_V_fig, E_x_V_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
        E_x_V_ax1.set_title(f"Eccentricity / Velocites n={n_str}")
        E_x_V_ax1.set_xlabel("Eccentricity")
        E_x_V_ax1.hist2d(
            stats.eccentricities[mask],
            stats.velocities[mask],
            150,
            ((0, 1), (0, 0.1)),
            norm=colors.LogNorm(),
        )
        E_x_V_fig.savefig(experiment_dir / "eccentricity_x_velocity-histogram.png")

        E_x_O_fig, E_x_O_ax1 = plt.subplots(figsize=figsize, dpi=dpi, tight_layout=True)
        E_x_O_ax1.set_title(f"Orientation / Eccentricity n={n_str}")
        E_x_O_ax1.set_xlabel("Orientation (radians)")
        E_x_O_ax1.hist2d(
            stats.orientations[mask],
            stats.eccentricities[mask],
            150,
            ((-1.8, 1.8), (0, 1)),
            norm=colors.LogNorm(),
        )
        E_x_O_fig.savefig(experiment_dir / "orientation_x_eccentricity-histogram.png")

        plt.subplot(231)
        plt.title(f"Eccentricities")
        plt.hist(stats.eccentricities[mask], 50, (0, 1))
        plt.subplot(232)
        plt.title(f"Orientations n={n_str}")
        plt.hist(stats.orientations[mask], 135, (-(np.pi / 2), +(np.pi / 2)))
        plt.subplot(233)
        plt.title(f"Velocities")
        plt.hist(stats.velocities[mask], 50, (0, 0.1))

        plt.subplot(234)
        plt.title("Areas")
        plt.hist(stats.areas_by_diameter[mask], 50, (0, 25e4))

        plt.subplot(235)
        plt.title("Areas/Vel")
        plt.hist2d(
            stats.areas_by_diameter[mask],
            stats.velocities[mask],
            150,
            ((0, 25e4), (0, 0.1)),
            norm=colors.LogNorm(),
        )

        plt.subplot(236)
        plt.title("Ecc/Or")
        plt.hist2d(
            stats.orientations[mask],
            stats.eccentricities[mask],
            150,
            ((-1.8, 1.8), (0, 1)),
            norm=colors.LogNorm(),
        )

        plt.savefig(experiment_dir / "summary.png", bbox_inches="tight", dpi=300)

        print("Plots generated")

    except Exception as e:
        import traceback

        print("Error, rolling back changes.", e)
        print(
            "".join(
                traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
            )
        )
        await transaction.rollback()
        if os.path.exists(experiment_dir):
            print("Removing files from", experiment_dir)
            shutil.rmtree(experiment_dir)
    else:
        print("Success")
        await transaction.commit()

    finally:
        print("All done")


def collage_crops(ls, p):

    bb = p.bbox
    n_sq = 3

    w, h = bb[3] - bb[1], bb[2] - bb[0]
    crop = np.zeros((64 + h, max(w * 2, 64 * n_sq), 3), dtype="uint8")

    div = ls.dv[bb[0] : bb[2], bb[1] : bb[3]]
    div_r = imresize(div, size=(64, 64))  # , mode="bicubic")

    vis = ls.im[bb[0] : bb[2], bb[1] : bb[3]]
    vis_r = imresize(vis, size=(64, 64))

    mk = 255 * ls.mk[bb[0] : bb[2], bb[1] : bb[3]]
    mk_r = np.dstack([imresize(mk, size=(64, 64))] * 3)

    crop[0:64, 0 : (64 * n_sq), :] = np.concatenate([vis_r, div_r, mk_r], axis=1)
    crop[64 : (64 + h), 0:w, :] = vis
    crop[64 : (64 + h), w : (w * 2), :] = div

    return crop


class DB_CSV:

    def __init__(tx, table, columns):
        import tempfile

        self.table = table
        self.columns = columns
        self.fp, self.fname = tempfile.mkstemp()

    def insert(data):
        self.fp.write("\t".join(map(str, data)))

    async def commit(tx, cleanup=True):
        await self.tx.execute(
            "COPY {} ( {} ) FROM {} FORMAT text".format(
                self.table, ", ".join(columns), self.fname
            )
        )
        if cleanup:
            self.cleanup()

    def cleanup():
        os.unlink(self.fp)
