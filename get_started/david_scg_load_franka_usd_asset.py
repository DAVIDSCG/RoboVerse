# edited from scripts/test_usd.py


from __future__ import annotations

#########################################
### 1. Add command line arguments
#########################################
from dataclasses import dataclass

import tyro


@dataclass
class Args:
    usd_path: str = "roboverse_data/robots/franka/usd/franka_v2.usd"
    """The path to the USD file to load"""
    articulation: bool = True
    """Whether to load as articulation object"""
    fix_texture: bool = True
    """Whether to fix the materials"""
    ground: bool = False  # 目前可能由于系统的问题，减少问题源
    """Whether to add ground"""
    gravity: bool = False
    """Whether to enable gravity"""
    init_pos: tuple[float, float, float] = (0.0, 0.0, 0.0)
    """The initial position of the object"""


args = tyro.cli(Args)


#########################################
### 2. Launch IsaacLab
#########################################
def launch_isaaclab():
    import argparse

    from isaaclab.app import AppLauncher  # for isaaclab2 API

    parser = argparse.ArgumentParser()
    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args([])
    app_launcher = AppLauncher(args)
    simulation_app = app_launcher.app
    return simulation_app


simulation_app = launch_isaaclab()

#########################################
### 3. Normal code
#########################################

import isaaclab.sim as sim_utils  # for isaaclab2 API
import omni
from isaaclab.assets import (
    Articulation,
    ArticulationCfg,
)
from loguru import logger as log
from pxr import PhysxSchema
from rich.logging import RichHandler

try:
    import omni.isaac.core.utils.prims as prim_utils
except ModuleNotFoundError:
    import isaacsim.core.utils.prims as prim_utils

from metasim.sim.isaaclab.utils.ground_util import create_ground, set_ground_material, set_ground_material_scale
from metasim.sim.isaaclab.utils.usd_util import ShaderFixer

log.configure(handlers=[{"sink": RichHandler(), "format": "{message}"}])


def design_scene():
    # spawn distant light
    cfg_light_distant = sim_utils.DistantLightCfg(
        intensity=3000.0,
        color=(0.75, 0.75, 0.75),
    )
    # cfg_light_distant = sim_utils.DomeLightCfg(intensity=3000.0, texture_file="/home/haoran/Downloads/lebombo_4k.hdr")
    cfg_light_distant.func("/World/lightDistant", cfg_light_distant, translation=(1, 0, 10))

    # create a new xform prim for all objects to be spawned under
    prim_utils.create_prim("/World/Objects", "Xform")

    # add objects you want to test
    if args.articulation:
        Articulation(
            ArticulationCfg(
                prim_path="/World/panda",
                spawn=sim_utils.UsdFileCfg(usd_path=args.usd_path),
                actuators={},
                init_state=ArticulationCfg.InitialStateCfg(
                    pos=args.init_pos,
                ),
            )
        )

    # tests
    if args.fix_texture:
        fixer = ShaderFixer(args.usd_path, "/World/panda")
        fixer.fix_all()


# 目前不执行
def design_ground():
    create_ground()
    set_ground_material(material_mdl_path="data_isaaclab/source_data/arnold/materials/Wood/Ash.mdl")  # 暂时不存在
    set_ground_material_scale((10.0, 10.0))


def disable_gravity():
    stage = omni.usd.get_context().get_stage()
    prim = stage.GetPrimAtPath("/World/panda")
    physxAPI = PhysxSchema.PhysxRigidBodyAPI.Apply(prim)
    physxAPI.CreateDisableGravityAttr(True)


def main():
    """Main function."""

    # Initialize the simulation context
    sim_cfg = sim_utils.SimulationCfg(dt=0.01, device="cuda")
    sim = sim_utils.SimulationContext(sim_cfg)
    sim.set_camera_view([1.0, 0.0, 1.0], [0.0, 0.0, 0.0])

    if args.ground:
        design_ground()
    design_scene()
    if not args.gravity:
        disable_gravity()

    log.info("Starting simulation")
    sim.reset()
    while simulation_app.is_running():
        sim.step()


if __name__ == "__main__":
    main()
    simulation_app.close()
