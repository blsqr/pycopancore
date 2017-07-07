""" """

# This file is part of pycopancore.
#
# Copyright (C) 2016 by COPAN team at Potsdam Institute for Climate
# Impact Research
#
# URL: <http://www.pik-potsdam.de/copan/software>
# License: MIT license


# TODO: rename to ScipyODERunner

from .. import Event, Step, Variable
from ..private import _AbstractRunner, _DotConstruct, eval, unknown, \
    _AbstractEntityMixin
# TODO: discuss whether this makes sense or leads to problems:
from .hooks import Hooks

from scipy import integrate
import numpy as np

from time import time
# import sys

# from profilehooks import coverage, profile


class Runner(_AbstractRunner):
    """Runner-class, it owns the run function which calculates trajectories.

    Equations might be of type ODE, explicit, step and event, as stated in the
    process_types package.
    """

    _current_iteration = None
    """counter for expression evaluation cache"""

    def __init__(self,
                 model,
                 *,
                 termination_calls=None
                 ):
        """Instantiate a Runner.

        Parameters
        ----------
        model : Model
            The model to be run.
        termination_calls : list, optional
            List of lists of callables and instances on which they are to be
            called to determine if the runner should terminate in special
            cases prior to the time limit.
        kwargs
        """
        super(Runner, self).__init__()

        # register model and for performance reasons also some of its
        # properties as runner attributes:
        self.model = model
        self.processes = model.processes
        self.explicit_processes = model.explicit_processes
        self.event_processes = model.event_processes
        self.step_processes = model.step_processes
        self.ode_processes = model.ODE_processes
        self.trajectory_dict = {}

        self.termination_calls = termination_calls

        # initialize counter:
        self._current_iteration = 0

#    @profile  # generates time profiling information
    def apply_explicits(self, t):
        """Apply all Explicit processes.

        Parameters
        ----------
        t : float
            Model time
        """
        # TODO: apply them in an order that respects dependencies among
        # variables! for this, determine dependency structure in
        # modellogics.configure!
        for p in self.explicit_processes:
            spec = p.specification  # either a list of symbolic expressions or a method
            if isinstance(spec, list):
                # it's a list of symbolic expressions, one for each target in
                # the same order as in "targets". hence we loop over those:
                for i, target in enumerate(p.targets):
                    # evaluate corresponding expression,
                    # giving a list of values, one for each instance,
                    # in an order determined by the target:
                    values = eval(spec[i],
                                  self._current_iteration)
                    # note that values may have different length than
                    # p.owning_class.instances due to broadcasting effects
                    # if the target is a dotconstruct.
                    # store values in these target instances:
                    target.fast_set_values(values)
            else:  # it's a method
                # call process' implementation method for each of its
                # owning class' (!) instances. This will store values in
                # the target (!) instances' attributes directly:
                for inst in p.owning_class.instances:
                    spec(inst, t)

#    @profile  # generates time profiling information
    def get_rhs_array(self,
                      t, value_array  # this order is correct for use with scipy.ode class!
                      # value_array, t  # this order would be correct for use with scipy.odeint function
                      ):
        """Return RHS of composite ODE system as an array.

        Will be passed to scipy.ode class.

        Parameters
        ----------
        t : float
            Model time
        value_array : array
            array of variable values

        Returns
        -------
        array
            array of derivatives in same order as value_array
        """
        self._current_iteration += 1  # marks current evaluation caches as outdated

        # Execute all explicit processes (3.1.2 in runner scheme):
        self.apply_explicits(t)
        # TODO: for speedup, only do this for those explicits whose targets
        # are needed during ODE integration, and execute all others ex post.

        # copy values from value_array into instance attributes,
        # and clear target instances' derivative attributes:
        for target in self.model.ODE_targets:
            var = target.target_variable
            # use the values stored in the slice of value_array specified
            # by the target's _from and _to attributes:
            var.fast_set_values(values=value_array[target._from:target._to])
            var.clear_derivatives()

        # let all processes calculate their derivative terms:
        derivative_array = np.zeros(value_array.size)
        for p in self.ode_processes:
            spec = p.specification
            if isinstance(spec, list):
                # its a list of symbolic expressions, one for each target:
                for i, target in enumerate(p.targets):
                    # evaluate symbolic expression for each target instance,
                    # giving a list:
                    summands = eval(spec[i], self._current_iteration)
                    if isinstance(target, Variable):
                        # add result directly to output array
                        # (rather than in instances' derivative attributes):
                        derivative_array[target._from:target._to] += summands
                    else:
                        # summands may have different length than
                        # p.owning_class.instances due to broadcasting effects
                        # if target is a dotconstruct,
                        # hence we cannot simply copy it into the
                        # derivative_array array slice target._from:target._to.
                        # instead, we add terms directly to target instances'
                        # derivative attributes where they will be read from
                        # later:
                        target.add_derivatives(summands)
                        # TODO: use an njitted function add2array(array,
                        # positions, values) and expr._target_positions based
                        # on a new entity attribute _index
                        # that marks the position in the ordered set entities.
                        # when an entity is removed from this set, move the one
                        # at the last position to the freed position.
            else:
                # call process' implementation method for each of it's
                # owning class' (!) instances. This will add terms to
                # the target (!) instances' derivative attributes:
                for inst in p.owning_class.instances:
                    spec(inst, t)

        # add derivative terms from derivative attributes to output array
        # at same positions:
        for target in self.model.ODE_targets:
            derivative_array[target._from:target._to] += \
                target.target_variable.get_derivatives(
                            instances=target.target_class.instances)

        return derivative_array

    # @profile
    def run(self,
            *,
            t_0=0,
            t_1,
            dt  # TODO: rename to "resolution" since it is only an upper bound?
            # TODO: add some kwargs for choosing solver and setting its params
            ):
        """Run the model for a specified time interval.

        Run the model by simulating all processes in the right order in a way
        depending on process type (ODE integration, time stepping, etc.).

        Parameters
        ----------
        t_0 : float, optional
            Starting time (default: 0)
        t_1 : float
            End time
        dt : float
            Maximal interval between output time points

        Returns
        -------
        trajectory_dict: dict
            Model trajectory in requested time interval.
            Keys: 't' (contains the list of time points)
                and each Variable object simulated.
            Value of trajectory_dict[var]: dict with
                key: entity or taxon,
                value: list of variable values in same order as time points.
        """
        print("\nRunning from", t_0, "to", t_1, "with output at least every",
              dt, "...")

        # Initialize running time variable to starting time:
        t = t_0

        # For performance reasons, convert all variable values to standard
        # units, so that no DimensionalQuantities are left in variable values:
        self.model.convert_to_standard_units()

        # Create output dictionary:
        self.trajectory_dict = {v: {} for v in self.model.variables}

        # Save initial state to output dict:
        self.trajectory_dict['t'] = [t]
        self.save_to_traj(self.model.process_targets)
        # TODO: have save_to_traj() save t as well to have this cleaner.

        # Create dictionary containing discontinuities:
        next_discontinuities = {}

        # Apply all Explicit processes (2.2 in runner scheme)
        print("  Initial application of Explicit processes...")
        self.apply_explicits(t_0)

        # TODO: discuss whether hooks make sense, then maybe:
        # TODO: add hooks to runner scheme
        # apply all pre-hooks
        if Hooks._pre_hooks:
            print("  Executing pre-hooks ...")
            Hooks.execute_hooks(Hooks.Types.pre, self.model, t_0)

        # Find first occurrence times of events (2.3 in runner scheme):
        print("  Finding times of first occurrence of Events...")
        for event in self.event_processes:
            print("    Event process", event, "...")
            eventtype = event.specification[0]
            rate_or_timefunc = event.specification[1]
            # TODO: Check if the following loop is correct:
            for inst in event.owning_class.instances:
                # inst is a process taxon or entity
                assert eventtype in ("rate", "time"), \
                    "unsupported type of Event"
                if eventtype == "rate":
                    assert rate_or_timefunc > 0, \
                        "zero, negative, or varying rates not supported yet."
                    next_time = t_0 + np.random.exponential(1. / rate_or_timefunc)
                    # TODO: if rate_or_timefunc is a function in this case,
                    # it returns a time-varying rate that depends on state,
                    # hence it must be used in ode integration to integrate
                    # its cumulative distribution function, and when the
                    # latter crosses a threshold that we randomly draw
                    # here, solout must terminate (see below).
                elif eventtype == "time":
                    # in this case, rate_or_timefunc directly returns a time:
                    next_time = rate_or_timefunc(t)
                    assert next_time > t_0, "next time must be > t"
                try:
                    next_discontinuities[next_time].append((event, inst))
                except KeyError:
                    next_discontinuities[next_time] = [(event, inst)]
                print("      time", next_time, ":", inst)

        # Fill next_discontinuities with times of next steps and perform
        # a step if necessary (still 2.3 in runner scheme):
        print("  Executing Steps and finding times of next execution...")
        for step in self.step_processes:
            print("    Step process", step, "...")
            next_time_func = step.specification[0]
            method = step.specification[1]
            for inst in step.owning_class.instances:
                # inst is a process taxon or entity
                # FIXME: it seems inconsistent how we currently deal with the
                # question whether a step exectutes at t_0 since it is unclear
                # how the step would indicate that it is so.
                # if next_time_func(inst, t) gives the smallest stepping time
                # AFTER t, the following check would be incorrect:
                if next_time_func(inst, t_0) == t_0:
                    # so this step occurs right at the beginning
                    method(inst, t)
                    # ask process when it steps next:
                    next_time = next_time_func(inst, t)
                    assert next_time > t_0, "next time must be > t"
                # TODO: Same time for all instances? self. necessary?
                else:
                    # ask process when it steps next:
                    next_time = next_time_func(inst, t)
                    assert next_time > t_0, "next time must be > t"
                # register next stepping time in dict:
                try:
                    next_discontinuities[next_time].append((step, inst))
                    # so there were already events at the same time
                except KeyError:
                    # so there was no event yet at that time
                    next_discontinuities[next_time] = [(step, inst)]
                print("      time", next_time, ":", inst)

        # At this point, no application of Explicit processes is necessary
        # since that is done during ODE integration

        # prepare ODE solver:
        solver = integrate.ode(self.get_rhs_array)
        # apparently dopri5 is faster than vode, so we use dopri5.
        # in vode, choosing bdf or adams doesn't seem to make any difference
        # solver.set_integrator("vode", max_step=dt, method="bdf")
        solver.set_integrator("dopri5",  # TODO: make this a parameter?
                              max_step=dt,
                              verbosity=1,
                              nsteps=10000  # TODO: make this a parameter?
                              )

        # running lists of times and solutions:
        times = []
        sol = []

        # callback function the solver calls to output solutions:
        def solout(sol_t, sol_valuearray):
            """Save solution of solver at one time point.

            Parameters
            ----------
            sol_t : float
                Model time
            sol_valuearray : array
                array of variable values in same order as for get_rhs_array
            """
            # save solution to lists:
            times.append(sol_t)
            sol.append(sol_valuearray.copy())
            # TODO: this is the place to implement termination
            # due to events without a priori known occurrence
            # time! if solout returns 0 (or -1?), solver will
            # terminate. Similarly for solver "vode" above
            print("      t =", sol_t, "            ", end='\r')
            # TODO: return value??
        solver.set_solout(solout)

        # Now loop until end time or early termination is reached:
        while t < t_1:
            # check whether to terminate early:
            if self.terminate():
                print('Terminating run early at time ', t)
                break
            # Get next discontinuity to find the next timestep where something
            # happens.
            # If there are no discontinuities, the next_discontinuities
            # dict is empty, therefore try is necessary:
            try:
                next_time = min(next_discontinuities.keys())  # TODO: speed-up by using different data type for next_discontinuities, something like OrderedDict?
            except ValueError:
                next_time = t_1

            # Call ode solver if there are any ODE processes:
            if self.model.ODE_processes:

                print("  Running smoothly from", t, "to", next_time, "...")

                # clear all targets _DotConstructs' caches of target instances
                # since events and steps may have changed instance references:
                for target in self.model.ODE_targets \
                        + self.model.explicit_targets:
                    target._target_instances = unknown

                # determine array layouts (froms and tos of slices)
                # and compose initial value-array:
                print("    Composing initial value array...")
                # list of array slice lengths, one for each target,
                # length equalling number of target instances:
                lens = [len(target.target_class.instances)
                        for target in self.model.ODE_targets]
                # upper slice index is given by cumulative sum of lens:
                tos = np.cumsum(lens)
                # lower slice index is previous slice's upper index:
                froms = np.concatenate(([0], tos[:-1]))
                # total array length:
                arraylen = sum(lens)
                # init the array:
                initial_array_ode = np.zeros(arraylen)
                for i, target in enumerate(self.model.ODE_targets):
                    # store slice indices in targets:
                    target._from = froms[i]
                    target._to = tos[i]
                    # get initial values from instances and store in array:
                    initial_array_ode[froms[i]:tos[i]] = \
                        target.target_variable.eval(
                                instances=target.target_class.instances)

                # In Odeint, call get_rhs_array to get the RHS of the ODE
                # system as an array (step 3.1 in runner scheme) then return
                # the trajectory (3.2 in runner scheme):

                print("    Calling ODE solver...")

                _starttime = time()  # for performance reporting

                times = []
                sol = []
                solver.set_initial_value(initial_array_ode, t)
                # now tell the solver to integrate from current time to
                # next_time. it will call solout at least every dt:
                solver.integrate(next_time)
                # now solout has filled the times and sol with the integration
                # result, so we can process them:
                ts = np.array(times)
                ode_trajectory = np.array(sol)

                # TODO: capture solver failures and report any errors!

                print("      ...took", time()-_starttime, "seconds and",
                      len(times), "time steps")

                # Save t values to output dict:
                self.trajectory_dict['t'] += list(ts)

                print("    Saving results to output dict...")
                # save trajectory of ODE variables to output dict:
                tlen = len(self.trajectory_dict['t'])  # no. of simulated time points
                for i, target in enumerate(self.model.ODE_targets):
                    # from this target's slice starting at column target._from,
                    # read results column by column and store in corresponding
                    # target instances:
                    for pos, inst in enumerate(target.target_class.instances):
                        # get this instance's value column as a list,
                        # containing the values for all time points:
                        values = list(
                                ode_trajectory[:, target._from + pos])
                        try:
                            if len(self.trajectory_dict[
                                       target.target_variable][inst]) < tlen:
                                # append to existing list:
                                self.trajectory_dict[
                                    target.target_variable][inst] += values
                        except KeyError:
                            # store as new list:
                            self.trajectory_dict[
                                target.target_variable][inst] = values

                # Take the time steps output by the ODE solver and apply
                # Explicit processes a posteriori (step 3.3 in runner scheme).
                # Save them to the trajectory_dict
                # This is only done if there are any Explicit processes.

                # TODO: in principle, this is inefficient since these processes
                # were applied already during ODE integration, only their
                # results were not stored. Can this be improved? Sadly, depen-
                # ding on the solver method, we might not be sure that when
                # solout is called, the previous call to apply_explicits was
                # for the same time point and state, so we cannot simply use
                # its result...

                if len(self.explicit_processes) > 0:
                    print("    Applying Explicit processes to simulated "
                          "time points...")
                    for pos, t in enumerate(ts):
                        # copy values from returned matrix to instances'
                        # attributes:
                        ode_values = ode_trajectory[pos, :]
                        # read values from result vector in same order as
                        # written into it:
                        for i, target in enumerate(self.model.ODE_targets):
                            target.target_variable.fast_set_values(
                                ode_values[target._from:target._to])
                        self.apply_explicits(t)
                        # complete the output dictionary:
                        self.save_to_traj(self.model.process_targets)

            # After all that is done, determine what happens at the
            # discontinuity (step 3.4 in runner scheme)
            # Delete the discontinuity from the dictionary and determine when
            # the next one happens:
            if len(next_discontinuities) > 0:

                # set current model time to end of previous ODE integration:
                t = next_time
                self.trajectory_dict['t'].append(t)

                print("  Executing Steps and/or Events at", t, "...")

                # loop over all co-occurring steps/events.
                # TODO: determine a "correct" order of steps/events or deal
                # in some other way with the problem of co-occurrence and
                # potential mutual dependences, including the potential
                # (de)activation of entities.
                for discontinuity in next_discontinuities.pop(t):
                    # print('        Entering the dicontinuity loop, t=', t)
                    # discontinuity is a tuple (event/step, entity/taxon)
                    process = discontinuity[0]
                    inst = discontinuity[1]
                    if isinstance(process, Event):
                        print("    Event", process, "@", inst, "...")
                        eventtype = process.specification[0]
                        rate_or_timefunc = process.specification[1]
                        method = process.specification[2]
                        # Perform the event by calling its implementation method:
                        method(inst, t)
                        # determine this event's next occurrence:
                        if eventtype == "rate":
                            # draw time from exponential distribution:
                            next_time = t + \
                                        np.random.exponential(1. /
                                                              rate_or_timefunc)
                        elif eventtype == "time":
                            # ask event when it next happens:
                            next_time = rate_or_timefunc(t)
                            assert next_time > t, "next time must be > t"
                        # register it:
                        try:
                            next_discontinuities[next_time].append((process,
                                                                    inst))
                        except KeyError:
                            next_discontinuities[next_time] = [(process,
                                                                inst)]
                        print("      next time", next_time)
                    elif isinstance(process, Step):
                        print("    Step", process, "@", inst, "...")
                        timefunc = process.specification[0]
                        method = process.specification[1]
                        # Perform the step by calling its implementation method:
                        method(inst, t)
                        # determine this event's next occurrence:
                        next_time = timefunc(inst, t)
                        assert next_time > t, "next time must be > t"
                        # register it:
                        try:
                            next_discontinuities[next_time].append((process,
                                                                    inst))
                        except KeyError:
                            next_discontinuities[next_time] = [(process,
                                                                inst)]
                        print("      next time", next_time)

                # Complete the new state by applying all explicit processes
                # (3.5 in runner scheme):
                print("    Applying Explicit processes to changed state...")
                if self.model.explicit_processes:
                    self.apply_explicits(t)

                # Store all information that has been calculated at time t:
                print("    Completing output dict...")
                self.save_to_traj(self.model.process_targets)

            # TODO: discuss whether hooks make sense, then maybe:
            # TODO: add hooks to runner scheme
            # apply all mid-hooks
            if Hooks._mid_hooks:
                print("  Executing mid-hooks ...")
                Hooks.execute_hooks(Hooks.Types.mid, self.model, t_0)

        # TODO: discuss whether hooks make sense, then maybe:
        # TODO: add hooks to runner scheme
        # apply all post-hooks
        if Hooks._post_hooks:
            print("  Executing post-hooks ...")
            Hooks.execute_hooks(Hooks.Types.post, self.model, t_0)

        return self.trajectory_dict

    def save_to_traj(self, targets):
        """Save simulation results to output dictionary.

        Update self.trajectory_dict for some targets.

        Parameters
        ----------
        targets : list
            list of targets (variables or dotconstructs) to save
        """
        # determine no. of simulated time points:
        tlen = len(self.trajectory_dict["t"])
        for target in targets:
            # target is a variable or a dotconstruct
            var = target.target_variable
            instances = target.target_class.instances
            # Check for deactivated instances. The following check is
            # necessary, since Process Taxa cannot be inactive:
            if issubclass(target.target_class,
                          _AbstractEntityMixin):
                idle_instances = target.target_class.idle_entities
            # get values to store from instance attributes:
            values = var.eval(instances)

            # write values into all active Instances:
            for i, inst in enumerate(instances):
                try:
                    # check whether value needs to be stored by comparing
                    # existing list length with no. of time points:
                    if len(self.trajectory_dict[var][inst]) < tlen:
                        self.trajectory_dict[var][inst].append(values[i])
                    # else do nothing since value was already stored.
                except KeyError:
                    # This branch is active if the entity has not been
                    # activated before.
                    # create new list with Nones for time that has passed:
                    time_passed = [None] * (tlen - 1)
                    time_passed.append(values[i])
                    self.trajectory_dict[var][inst] = time_passed
                    assert len(self.trajectory_dict[var][inst]) == tlen

            # check if there are any idle instances and fill their trajectory
            # with None to fit he lenght of 't':
            if idle_instances:
                for i, inst in enumerate(idle_instances):
                    try:  # already in trajectory_dict
                        # Check for length of list:
                        if len(self.trajectory_dict[var][inst]) < tlen:
                            len_of_none = (
                                tlen - len(self.trajectory_dict[var][inst]))
                            none_list = [None]*len_of_none
                            # Make list as long as 't' in trajectory_dict:
                            for j in none_list:
                                self.trajectory_dict[var][inst].append(j)
                            # And make shure it has the length of 't'
                            assert len(self.trajectory_dict[var][inst]) == tlen
                    except KeyError:  # Not yet in trajectory_dict
                        # create new list:
                        none_list = [None]*tlen
                        self.trajectory_dict[var][inst] = [none_list]
                        assert len(self.trajectory_dict[var][inst]) == tlen

    def terminate(self):
        """Determine if the runner should stop.

        Apply all callables specified in self.termination_calls on their
        respective instances. If one of them indicates a termination condition
        by returning True, then return True. Else return False.

        Returns
        -------
        boolean
            True if the runner should stop according to one of the
            callables in self.termination_calls.
            False, if there are no such callables or if they all return False.
        """
        if self.termination_calls:
            for signal in self.termination_calls:
                method = signal[0]
                inst = signal[1]
                if method(inst):
                    return True
        return False
