#!/usr/bin/env python3

# Copyright (c) 2020, RTE (https://www.rte-france.com)
# See AUTHORS.txt
# This Source Code Form is subject to the terms of the Mozilla Public License, version 2.0.
# If a copy of the Mozilla Public License, version 2.0 was not distributed with this file,
# you can obtain one at http://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# This file is part of L2RPN Baselines, L2RPN Baselines a repository to host baselines for l2rpn competitions.

import argparse
import tensorflow as tf

from grid2op.MakeEnv import make2
from grid2op.Reward import *
from grid2op.Action import *


from DoubleDuelingRDQNAgent import DoubleDuelingRDQNAgent as RDQNAgent


def cli():
    parser = argparse.ArgumentParser(description="Train baseline DDQN")
    parser.add_argument("--path_data", required=True,
                        help="Path to the dataset root directory")
    parser.add_argument("--name", required=True,
                        help="The name of the model")
    parser.add_argument("--batch_size", required=False,
                        default=32, type=int,
                        help="Mini batch size (defaults to 32)")
    parser.add_argument("--num_pre_steps", required=False,
                        default=256, type=int,
                        help="Number of random steps before training")
    parser.add_argument("--num_train_steps", required=False,
                        default=1024, type=int,
                        help="Number of training iterations")
    parser.add_argument("--trace_len", required=False,
                        default=8, type=int,
                        help="Size of the trace to use during training")
    parser.add_argument("--learning_rate", required=False,
                        default=1e-5, type=float,
                        help="Learning rate for the Adam optimizer")
    parser.add_argument("--resume", required=False,
                        help="Path to model.h5 to resume training with")
    return parser.parse_args()


if __name__ == "__main__":
    # Get params from command line
    args = cli()

    env = make2(args.path_data,
                action_class=TopologyChangeAndDispatchAction,
                reward_class=CombinedReward,
                other_rewards={
                    "bridge": BridgeReward,
                    "overflow": CloseToOverflowReward,
                    "distance": DistanceReward
                })
    # Register custom reward for training
    cr = env.reward_helper.template_reward
    cr.addReward("bridge", BridgeReward(), 0.3)
    cr.addReward("overflow", CloseToOverflowReward(), 0.3)
    cr.addReward("distance", DistanceReward(), 0.3)
    cr.addReward("game", GameplayReward(), 1.0)
    #cr.addReward("redisp", RedispReward(), 2.5e-4)
    # Initialize custom rewards
    cr.initialize(env)

    # Limit gpu usage
    physical_devices = tf.config.list_physical_devices('GPU')
    tf.config.experimental.set_memory_growth(physical_devices[0], True)

    agent = RDQNAgent(env, env.action_space,
                      name=args.name, 
                      batch_size=args.batch_size,
                      trace_length=args.trace_len,
                      is_training=True,
                      lr=args.learning_rate)

    if args.resume is not None:
        agent.load_network(args.resume)

    agent.train(args.num_pre_steps, args.num_train_steps)
