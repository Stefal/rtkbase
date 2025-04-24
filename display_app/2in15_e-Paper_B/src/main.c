#include <stdio.h>
#include <stdlib.h>    
#include <signal.h>    
#include <sys/stat.h>
#include "EPD_2in15b_Manager.h"
#include "duos_pinmux.h"

void Handler(int signo)
{
    //System Exit
    printf("\r\nHandler:exit\r\n");
    DEV_Module_Exit();

    exit(0);
}

static int validate_file(const char *path)
{
    struct stat sb;

    if (path == NULL || path[0] == '\0') {
        Debug("Error: empty filename\n");
        return 0;
    }
    if (stat(path, &sb) != 0) {
        perror(path);
        return 0;
    }
    if (!S_ISREG(sb.st_mode)) {
        Debug("Error: %s is not a regular file\n", path);
        return 0;
    }
    return 1;
}

int main(int argc, char *argv[])
{
    const char *file1;
    const char *file2;

    /* 1) Check that exactly two arguments were provided */
    if (argc != 3) {
        Debug("Usage: %s <image_red.bmp> <image_black.bmp>\n", argv[0]);
        return EXIT_FAILURE;
    }
    file1 = argv[1];
    file2 = argv[2];

    /* 2) Validate each file */
    if (!validate_file(file1) || !validate_file(file2)) {
        return EXIT_FAILURE;
    }

    /* 3) Setup Ctrl+C handler */
    signal(SIGINT, Handler);

    /* 4) Configure pinmux */
    duos_pinmux("B13", "SPI3_SDO");
    duos_pinmux("B14", "B14");
    duos_pinmux("B15", "SPI3_SCK");
    duos_pinmux("B16", "B16");
    duos_pinmux("B22", "B22");
    duos_pinmux("B20", "B20");
    duos_pinmux("B18", "B18");

    if (EPD_2in15b_Manager(file1, file2) != 0) {
        Debug("EPD_2in15b_Manager failed for %s and %s\n", file1, file2);
        return EXIT_FAILURE;
    }

    return EXIT_SUCCESS;
}
