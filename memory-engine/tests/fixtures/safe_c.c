/*
 * Fichier C sans vulnérabilités — le moteur doit retourner 0 findings
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void safe_copy(const char *input) {
    char buf[64];
    strncpy(buf, input, sizeof(buf) - 1);
    buf[sizeof(buf) - 1] = '\0';
    printf("User: %s\n", buf);
}

char *safe_alloc(size_t n) {
    char *p = malloc(n);
    if (!p) {
        fprintf(stderr, "malloc failed\n");
        return NULL;
    }
    return p;
}

int main() {
    safe_copy("hello");
    char *buf = safe_alloc(128);
    if (buf) {
        snprintf(buf, 128, "value=%d", 42);
        printf("%s\n", buf);
        free(buf);
        buf = NULL;
    }
    return 0;
}
