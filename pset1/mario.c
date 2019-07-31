#include <stdio.h>
#include <cs50.h>

int main(void){
  int height, space;

  do{ height = get_int("HEIGHT: "); } while(height <= 0 || height >= 9);

  space = height;

  for(int totalOfBricks=0; totalOfBricks<height; totalOfBricks++){

    for(int k=1; k<space; k++) { printf(" "); }

    for(int leftBricks=0; leftBricks<=totalOfBricks; leftBricks++) {printf("#");}

    printf("  ");

    for(int rightBricks=0; rightBricks<=totalOfBricks; rightBricks++) {printf("#");}

    printf("\n");

    space--;
  }

}
