/*
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is:  none.
 *
 * Contributor(s): Enrico Fracasso
 *
 * ***** END GPL LICENSE BLOCK *****
 * wrapper used to run webplugin with lower privilage: it must be setuid root
 */


// Enabling O_NOFOLLOW
#define _GNU_SOURCE

#include <stdio.h>
#include <unistd.h>

#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

#include <pwd.h>
#include <stdlib.h> // exit
#include <string.h> // memcpy

#include <signal.h>

// the blenderplayer id (used by sigterm_handler handler)
pid_t blenderplayer_id = 0;



void print_id()
{
	uid_t ruid, euid, suid;

	getresuid(&ruid, &euid, &suid);
	printf("Real UID %d, Effective UID %d, Saved UID %d\n", ruid, euid, suid);

}

/**
	This function is used to catch SIGTERM signal (raised by web plugin when the plugin should shut down
	and raise a SIGKILL signal to the blenderplayer in order to kill it.
*/
void sigterm_handler(int signum)
{
	printf("Signal!!!\n");
	if (blenderplayer_id != 0) {
		kill(blenderplayer_id, SIGKILL);
		printf("Signal sent!!!\n");
	}
	
}

/**
	Run blenderplayer sandboxed. 
	It has two parameters
	argv[1] should be a file name
	argv[2] should be an window handle id

*/
int main(int argc, char *argv[])
{
	uid_t privid = geteuid();
	uid_t caller_id = getuid();

	/** This code runs with elevated privileges   */

	struct passwd *pw;
	pw = getpwnam("nobody"); // make it a param on a config file
	uid_t  new_id = pw->pw_uid;

	if (argc != 3) {
		fprintf(stderr, "I need two parameters on command line!\n");
		exit(EXIT_FAILURE);
	}

	/* If the caller is the owner of the file, chown to the privsep user */
	const char* file_name = argv[1];
	const char* window_id = argv[2];
	fprintf(stderr, "File name: %s XID: %s\n", file_name, window_id);

	struct stat stat_data;

	int fd = open(file_name, O_NOFOLLOW);
	if (fd == -1 ) {
		perror("Cannot open file\n");
		exit(EXIT_FAILURE);
	}
	
	if (fstat(fd, &stat_data) != 0) {
		perror("Cannot read file\n");
		exit(EXIT_FAILURE);
	}

	if (stat_data.st_uid != caller_id) {
		printf("File not owned by the caller\n");
		exit(EXIT_FAILURE);
	}

	if (!S_ISREG(stat_data.st_mode)) {
		printf("File is not a regular file\n");
		exit(EXIT_FAILURE);
	}

	if (fchown(fd, new_id, -1) != 0 ){
		perror("Cannot chown file\n");
		exit(EXIT_FAILURE);
	}
	
	if ( close(fd) != 0) {
		perror("Cannot close file\n");
		exit(EXIT_FAILURE);
	}


	/* creating Xlib xauth file */
	char template[] = "/tmp/blender-auth.XXXXXX";
	/* We need a temp file name only; file will be created by xauth later */
	char * auth_file_name = mktemp(template);

	const char* display = getenv("DISPLAY");
	if (display == NULL) {
		fprintf(stderr, "DISPLAY environment variable not found, aborting");
		exit(EXIT_FAILURE);
	}

	printf("Forking auth....\n");
	pid_t id_auth = fork();

	if (id_auth == 0) { //child 

		/* I want to run xauth as caller user */
		if (setuid(caller_id) != 0) {
			perror("Cannot drop privilages!\n");
			exit(EXIT_FAILURE);
		}

		
		if (setuid(0) != -1) {
			perror("Privilages can be restored!\n");
			exit(EXIT_FAILURE);
		}

		print_id();	
	
		int e = execlp ("xauth", "xauth", "-f", auth_file_name, "generate", display, ".", "trusted", (char*)NULL);
		perror("Error executing xauth!\n"); 
		exit(EXIT_FAILURE);

	} if (id_auth < 0 )  { //error
		perror("Cannot fork!\n");
		exit(EXIT_FAILURE);
	
	}
	else { // parent
		int status;
		fprintf(stderr, "Waiting for xauth....\n");
		wait(&status);
		fprintf(stderr, "Done!\n");
	}

	/* xauth file must be readable by the privsep user */
	if (chown(auth_file_name, new_id, -1) != 0 ){
		perror("Cannot chown auth file\n");
		exit(EXIT_FAILURE);
	}

	signal(SIGTERM, sigterm_handler);
	print_id();	

	blenderplayer_id = fork();
	if (blenderplayer_id == 0 ) { //child
		
		/** Drop privileges */
		
		if (setuid(new_id) != 0) {
			perror("Cannot drop privilages!\n");
			exit(EXIT_FAILURE);
		}
		
		if (setuid(0) != -1) {
			perror("Privilages can be restored!\n");
			exit(EXIT_FAILURE);
		}
		
		print_id();
		fprintf(stderr, "Privilages dropped successfully\n");
	
		setenv("XAUTHORITY", auth_file_name, 1);
	
		const char* blenderplayer = "/usr/bin/blenderplayer";
		execl(blenderplayer, "blenderplayer", "-i", window_id, file_name, (char*)NULL);
	}
	else {
		/** Still running with higher privileges */
		int status;
		fprintf(stderr, "Waiting for blenderplayer....\n");
		wait(&status);
		fprintf(stderr, "blenderplayer done!\n");

		// We have to remove xauth file and I have to chown blender file back to the original user
		if (chown(file_name, caller_id, -1) != 0 ){
			perror("Cannot chown file back to original user\n");
			exit(EXIT_FAILURE);
		}

		if (unlink(auth_file_name) != 0) {
			perror("Cannot remove xauth file!\n");
			exit(EXIT_FAILURE);
		}
	
	}

	
}

