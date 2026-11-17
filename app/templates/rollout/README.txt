===============================================================================================================================

Rollout	:      <ROLLOUT_NUMBER>                               <CURENT_DATE_FILED>

Description: 

Issues Fixed: Issue(s) fixed, one per line.

===============================================================================================================================

Release notes for the fixes in this rollout.

===============================================================================================================================
                                     U N I X   I N S T A L L A T I O N   N O T E S             
===============================================================================================================================

1. Login as the environment's administrator.
2. Check for the below mentioned directories, create if not available
	$ cd $LESDIR/rollouts | if not available mkdir $LESDIR/rollouts
	$ mkdir <ROLLOUT_NUMBER>
	
3. Navigate to the temporary directory on the server to retain a copy of the rollout package for future reference.
	$ cd $LESDIR/temp
	$ mkdir $LESDIR/temp/<ROLLOUT_NUMBER>
	$ cd $LESDIR/temp/<ROLLOUT_NUMBER>
	
4. Copy the rollout distribution file from the temporary directory into the rollout directory and extract it
	$ cp $LESDIR/temp/<ROLLOUT_NUMBER>.zip $LESDIR/rollouts/<ROLLOUT_NUMBER>/<ROLLOUT_NUMBER>.zip
	$ cd $LESDIR/rollouts/<ROLLOUT_NUMBER>
	$ unzip <ROLLOUT_NUMBER>.zip

5. Shut down the RP environment.
	$ rp stop
	
6. Install the rollout.
	$ perl rollout.pl <ROLLOUT_NUMBER>

7.  Start up the environment.
    	$ rp start

===============================================================================================================================
                                 W I N D O W S   I N S T A L L A T I O N   N O T E S             
===============================================================================================================================

IF YOU ARE INSTALLING A HOTFIX CONTAINING RPWEB CHANGES PLEASE ALSO REFER BELOW

    1.  Start a Windows command prompt as an Administrator user

    2.  If compiling code, set Visual C++ environment variables.

        You will first have to change to the Visual C++ bin directory if it 
        isn't in your search path.

        vcvarsall.bat (OR vcvars32.bat OR vsvars32.bat for older versions of VS)

    3.  Set BY application environment variables.

        (2011.1 or earlier):
        cd %LESDIR%\data
          ..\..\moca\bin\servicemgr /env=<environment name> /dump
        env.bat

        (2011.2 or later):
          cd %LESDIR%\data
          ..\..\moca\bin\servicemgr -e <environment name> dump
          env.bat

        Note: If you know your env.bat file is current you can omit this step,
              if you are not sure then rebuild one.

    4.  Shutdown the MOCA server instance:  

        NON-CLUSTERED Environment

        *** IMPORTANT ***
        If you are on a production system, make sure the development system 
        whose drive has been mapped to the system being modified has also been 
        shutdown to avoid sharing violations.

        net stop moca.<environment name>

        (Or use the Windows Services snap-in to stop the MOCA service.

        CLUSTERED Environment
       
        If you are running under a Windows Server Cluster, you must use the
        Microsoft Cluster Administrator to stop the MOCA Service.

    5.  Copy the rollout distribution file into the environment's rollout 
        directory.

        cd -d %LESDIR%\rollouts
        copy <SOURCE_DIR>\<rollout folder> .

    6.  Uncompress the distribution file using your preferred unzip utility  

        Make sure you extract all the files to a folder.

    7.  Install the rollout.

        perl ./rollout.pl <rollout name>
    8.  Start up the MOCA instance:

        NON-CLUSTERED Environment
       
        net start moca.<environment name>

        (Or use the Windows Services snap-in to restart the MOCA service.

        CLUSTERED Environment

        If you are running under a Windows Server Cluster, you must use the
        Microsoft Cluster Administrator to start the MOCA Service.

===============================================================================================================================
					R P W E B    I N S T A L L A T I O N           
===============================================================================================================================

    If your rollout contains both server side and RPWEB changes you may see
    multiple control files with suffixes, e.g. ROLLOUTNAME_REFS.

    If you are running on a shared application/RPWEB server and the user account
    you are using has access to both instances you can use the default combined
    control file (e.g. ROLLOUTNAME).

    If your RPWEB instance is separate or your application server user account
    does not have permission to update RPWEB, then you should run the server
    control file (e.g. ROLLOUTNAME_LES or ROLLOUTNAME_DSS) under the server
    account and then copy the rollout to $REFSDIR/rollouts under the RPWEB user

    account and then also install from there using the ROLLOUTNAME_REFS
    control file. This will install the RPWEB only components in RPWEB.

===============================================================================================================================
                                        U N I N S T A L L   N O T E S                          
===============================================================================================================================

*** NOTES *** Attempting an uninstall of a rollout is not BY's recommended
    defect resolution path.  If an issue is found after applying
    a rollout BY highly recommends reporting the issue to BY so
    that a permanent fix can be determined.

    Any attempted uninstall should be first be thoroughly tested just
    as any other change to a production system.

*** STEPS ***

    1a.  If Windows complete steps 1-6 of the windows_install_notes.txt
    1b.  If Unix complete steps 1-4 of the linux_install_notes.txt

    2.  Open the rollout control file.

    3.  If the control file line begins with the keywords of ADD, REPLACE or REMOVE
        manually restore the previous version from the Install/backup directory or
		simply remove if there was no previous version to restore.

    4.  If the control file line begins with the keyword REBUILD a recompile
        is needed for the C and JAVA changes.  A "make" should be completed:
            (Windows): cd %LESDIR%
                       nmake -f makefile.nt

            (Unix):    cd $LESDIR
                       make

    5.  If the control file line begins with the keyword MBUILD a mbuild is
        needed for the MOCA changes.  A "mbuild" should be completed.

    6.  If the control file line begins with the keyword importsldata you should reload the previous
	    version of the transaction or remove it if it is new.

    7a.  If Windows complete step 8 of the windows_install_notes.txt
    7b.  If Unix complete step 6 of the linux_install_notes.txt

===============================================================================================================================
                                    E N D   O F   I N S T A L L A T I O N S   N O T E S                          
===============================================================================================================================