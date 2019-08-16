#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#include <unistd.h>
#include <stdlib.h>
#include <crypt.h>
#include <string.h>

#define MAX_LENGTH_HASH 256

bool isHashValid(char string[]);
bool isHashCracked(char hash[]);

int main(void){
  char userInput[MAX_LENGTH_HASH] = "";

  do{
    printf("enter hash: ");
    scanf("\n%[^\n]", userInput);
  }while(!isHashValid(userInput));

  if(!isHashCracked(userInput)){
    printf("hash could not be cracked.");
    return 1;
  }

  return 0;
}

bool isHashValid(char string[]){

  // check if user's input is null
  if(string[0] == '\0')
  {
    printf("invalid hash.\n");
    return false;
  }

  // check if user's input contains spaces
  for(int i=0, string_length = strlen(string); i < string_length; i++){
    if(string[i] == ' '){
      printf("invalid hash.\n");
      return false;
    }
  }

  return true;
}

bool isHashCracked(char hash[]){

  // letters that will be used to brute-force the hash input
  char letters[] = "\0abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";
  const int letters_count = 53;

  // in crypt(), the salt is always going to be the first two digits of the hash
  char salt[3];
  salt[0] = hash[0];
  salt[1] = hash[1];
  salt[2] = '\0';

  char possible_combinations[6] = "\0\0\0\0\0\0";

  for(int fifth = 0; fifth < letters_count; fifth++){
    for(int fourth = 0; fourth < letters_count; fourth++){
      for(int third = 0; third < letters_count; third++){
        for(int second = 0; second < letters_count; second++){
          for(int first = 0; first < letters_count; first++){
            possible_combinations[0] = letters[first];
            possible_combinations[1] = letters[second];
            possible_combinations[2] = letters[third];
            possible_combinations[3] = letters[fourth];
            possible_combinations[4] = letters[fifth];

            if(strcmp(crypt(possible_combinations, salt), hash) == 0){
              printf("hash cracked. password: %s\n", possible_combinations);
              return true;
            }
          }
        }
      }
    }
  }

  return false;
}
