#include <stdlib.h>     //exit()
#include <signal.h>     //signal()
#include "EPD_2in15b_Manager.h"   //Examples

void Handler(int signo)
{
    //System Exit
    printf("\r\nHandler:exit\r\n");
    DEV_Module_Exit();

    exit(0);
}

int main(void)
{
    // Exception handling:ctrl + c
    signal(SIGINT, Handler);

    EPD_2in15b_Manager(); 
    
    return 0;
}
