
def learn(policy, env, nsteps, total_timesteps, gamma,lam, vf_coef, ent_coef,
            lr, cliprange, max_grad_norm, log_interval):

    noptepochs = 4
    nminibatches = 8

    if isinstance(lr, float): lr = constfn(lr)
    else: assert callable(lr)
    if isinstance(cliprange, float): cliprange = constfn(cliprange)
    else: assert callable(cliprange)

    # Get the nb of env
    nenvs = env.num_envs

    # Get state_space and action_space
    ob_space = env.observation_space
    
    ac_space = env.action_space

    # Calculate the batch_size
    batch_size = nenvs * nsteps # For instance if we take 5 steps and we have 5 environments batch_size = 25

    batch_train_size = batch_size // nminibatches

    assert batch_size % nminibatches == 0

    # Instantiate the model object (that creates step_model and train_model)
    model = Model(policy=policy,
                ob_space=ob_space,
                action_space=ac_space,
                nenvs=nenvs,
                nsteps=nsteps,
                ent_coef=ent_coef,
                vf_coef=vf_coef,
                max_grad_norm=max_grad_norm)

    # Load the model
    # If you want to continue training
    # load_path = "./models/40/model.ckpt"
    # model.load(load_path)

    # Instantiate the runner object
    runner = Runner(env, model, nsteps=nsteps, total_timesteps=total_timesteps, gamma=gamma, lam=lam)

    # Start total timer
    tfirststart = time.time()

    nupdates = total_timesteps//batch_size+1

    for update in range(1, nupdates+1):
        # Start timer
        tstart = time.time()

        frac = 1.0 - (update - 1.0) / nupdates

        # Calculate the learning rate
        lrnow = lr(frac)

        # Calculate the cliprange
        cliprangenow = cliprange(frac)

        # Get minibatch
        obs, actions, returns, values, neglogpacs = runner.run()

        # Here what we're going to do is for each minibatch calculate the loss and append it.
        mb_losses = []
        total_batches_train = 0

        # Index of each element of batch_size
        # Create the indices array
        indices = np.arange(batch_size)

        for _ in range(noptepochs):
            # Randomize the indexes
            np.random.shuffle(indices)

            # 0 to batch_size with batch_train_size step
            for start in range(0, batch_size, batch_train_size):
                end = start + batch_train_size
                mbinds = indices[start:end]
                slices = (arr[mbinds] for arr in (obs, actions, returns, values, neglogpacs))
                mb_losses.append(model.train(*slices, lrnow, cliprangenow))
            

        # Feedforward --> get losses --> update
        lossvalues = np.mean(mb_losses, axis=0)

        # End timer
        tnow = time.time()

        # Calculate the fps (frame per second)
        fps = int(batch_size / (tnow - tstart))

        if update % log_interval == 0 or update == 1:
            """
            Computes fraction of variance that ypred explains about y.
            Returns 1 - Var[y-ypred] / Var[y]
            interpretation:
            ev=0  =>  might as well have predicted zero
            ev=1  =>  perfect prediction
            ev<0  =>  worse than just predicting zero
            """
            ev = explained_variance(values, returns)
            logger.record_tabular("serial_timesteps", update*nsteps)
            logger.record_tabular("nupdates", update)
            logger.record_tabular("total_timesteps", update*batch_size)
            logger.record_tabular("fps", fps)
            logger.record_tabular("policy_loss", float(lossvalues[0]))
            logger.record_tabular("policy_entropy", float(lossvalues[2]))
            logger.record_tabular("value_loss", float(lossvalues[1]))
            logger.record_tabular("explained_variance", float(ev))
            logger.record_tabular("time elapsed", float(tnow - tfirststart))
            
            savepath = "./models/" + str(update) + "/model.ckpt"
            model.save(savepath)
            print('Saving to', savepath)

            # Test our agent with 3 trials and mean the score
            # This will be useful to see if our agent is improving
            test_score = testing(model)

            logger.record_tabular("Mean score test level", test_score)
            logger.dump_tabular()
            
    env.close()
