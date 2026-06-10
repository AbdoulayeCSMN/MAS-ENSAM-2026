/*
 * Test fixture — fichier C volontairement vulnérable
 * Cible : MEM-001 strcpy, MEM-002 strcat, MEM-003 gets,
 *         MEM-004 sprintf, MEM-010 free, MEM-020 malloc, MEM-050 printf
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* MEM-001 : strcpy sans vérification de taille */
void copy_username(char *input) {
    char buf[64];
    strcpy(buf, input);   /* VULN: stack buffer overflow */
    printf("User: %s\n", buf);
}

/* MEM-002 : strcat sans vérification */
void build_path(char *dir, char *file) {
    char path[128];
    strcat(path, dir);    /* VULN: no bounds check */
    strcat(path, file);
}

/* MEM-003 : gets — toujours dangereux */
void read_input() {
    char buffer[32];
    gets(buffer);         /* VULN: unbounded read */
}

/* MEM-004 : sprintf sans snprintf */
void format_msg(char *user_data) {
    char msg[256];
    sprintf(msg, "Hello %s!", user_data);  /* VULN: potential overflow */
}

/* MEM-010 : use-after-free */
void process_data() {
    char *data = malloc(128);
    if (!data) return;
    strcpy(data, "hello");
    free(data);           /* VULN: data utilisé après free possible */
    printf("%s\n", data); /* use-after-free */
}

/* MEM-020 : malloc sans vérification NULL */
void allocate() {
    int n = 1000;
    char *buf = malloc(n * sizeof(char));  /* VULN: pas de check NULL */
    buf[0] = 'A';
}

/* MEM-050 : format string non contrôlée */
void log_message(char *user_input) {
    printf(user_input);   /* VULN: format string attack */
}

int main() {
    copy_username("test");
    return 0;
}
