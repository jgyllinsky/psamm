# This file is part of PSAMM.
#
# PSAMM is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PSAMM is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PSAMM.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2014-2015  Jon Lund Steffensen <jon_steffensen@uri.edu>
# Copyright 2016  Chao Liu <lcddzyx@gmail.com>

"""Implementation of fastGapFill.

Described in [Thiele14]_.
"""

from __future__ import unicode_literals

import logging

from six import iteritems
from .fastcore import fastcore

logger = logging.getLogger(__name__)


def create_extended_model(model, db_penalty=None, ex_penalty=None,
                          tp_penalty=None, penalties=None):
    """Create an extended model for FastGapFill algorithm.

    Create a :class:`psamm.metabolicmodel.MetabolicModel` with
    all reactions added (the reaction database in the model is taken
    to be the universal database) and also with artificial exchange
    and transport reactions added. Return the extended
    :class:`psamm.metabolicmodel.MetabolicModel`
    and a weight dictionary for added reactions in that model.

    Args:
        model: :class:`psamm.datasource.native.NativeModel`.
        db_penalty: penalty score for database reactions, default is `None`.
        ex_penalty: penalty score for exchange reactions, default is `None`.
        tb_penalty: penalty score for transport reactions, default is `None`.
        penalties: a dictionary of penalty scores for database reactions.
    """

    # Create metabolic model
    model_extended = model.create_metabolic_model()
    model_compartments = set(model_extended.compartments)
    extra_compartments = model.get_extracellular_compartment()

    # Add exchange and transport reactions to database
    logger.info('Adding database, exchange and transport reactions')
    db_added = model_extended.add_all_database_reactions(model_compartments)
    ex_added = model_extended.add_all_exchange_reactions(
        extra_compartments, allow_duplicates=True)
    tp_added = model_extended.add_all_transport_reactions(
        extra_compartments, allow_duplicates=True)

    # Add penalty weights on reactions
    weights = {}
    if db_penalty is not None:
        weights.update((rxnid, db_penalty) for rxnid in db_added)
    if tp_penalty is not None:
        weights.update((rxnid, tp_penalty) for rxnid in tp_added)
    if ex_penalty is not None:
        weights.update((rxnid, ex_penalty) for rxnid in ex_added)

    if penalties is not None:
        for rxnid, penalty in iteritems(penalties):
            weights[rxnid] = penalty
    return model_extended, weights


def fastgapfill(model_extended, core, solver, weights={}, epsilon=1e-5):
    """Run FastGapFill gap-filling algorithm by calling
    :func:`psamm.fastcore.fastcore`.

    FastGapFill will try to find a minimum subset of reactions that includes
    the core reactions and it also has no blocked reactions.
    Return the set of reactions in the minimum subset. An extended model that
    includes artificial transport and exchange reactions can be generated by
    calling :func:`.create_extended_model`.

    Args:
        model: :class:`psamm.metabolicmodel.MetabolicModel`.
        core: reactions in the original metabolic model.
        weights: a weight dictionary for reactions in the model.
        solver: linear programming library to use.
        epsilon: float number, threshold for Fastcore algorithm.
    """

    # Run Fastcore and print the induced reaction set
    logger.info('Calculating Fastcore induced set on model')
    induced = fastcore(
        model_extended, core, epsilon=1e-5, weights=weights, solver=solver)
    logger.info('Result: |A| = {}, A = {}'.format(len(induced), induced))
    added_reactions = induced - core
    logger.info('Extended: |E| = {}, E = {}'.format(
        len(added_reactions), added_reactions))
    return induced