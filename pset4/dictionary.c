// Implements a dictionary's functionality

#include <ctype.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "dictionary.h"

// Represents number of buckets in a hash table
#define N 26

int alphabetPosition(char firstLetter);
bool loaded = false;

// Represents a node in a hash table
typedef struct node
{
    char word[LENGTH + 1];
    struct node *next;
}
node;

// Represents a hash table
node *hashtable[N];

// keeps track of how many words have been loaded/checked
unsigned long words = 0;

const char alphabet[] = "abcdefghijklmnopqrstuvwxyz\0";

// Hashes word to a number between 0 and 25, inclusive, based on its first letter
unsigned int hash(const char *word)
{
    return tolower(word[0]) - 'a';
}

// Loads dictionary into memory, returning true if successful else false
bool load(const char *dictionary)
{
    // Initialize hash table
    for (int i = 0; i < N; i++)
    {
        hashtable[i] = NULL;
    }

    // Open dictionary
    FILE *file = fopen(dictionary, "r");
    if (file == NULL)
    {
        unload();
        return false;
    }

    // Buffer for a word
    char word[LENGTH + 1];

    // Insert words into hash table
    while (fscanf(file, "%s", word) != EOF)
    {

        // for every word, we allocate enough memory for a node, that will carry the word
        node *new_node = malloc(sizeof(node));
        if(new_node == NULL) { printf("could not allocate memory.\n"); return false; }

        strcpy(new_node->word, word);
        new_node->next = NULL;

        // if it's the first time the node is being initialized, then set the first word in it
        if(!hashtable[alphabetPosition(word[0])]){
            hashtable[alphabetPosition(word[0])] = new_node;
        }
        else
        {
            new_node->next = hashtable[alphabetPosition(word[0])];
            hashtable[alphabetPosition(word[0])] = new_node;
        }

        words++;
    }

    loaded = true;
    // Close dictionary
    fclose(file);

    // Indicate success
    return true;
}

// Returns number of words in dictionary if loaded else 0 if not yet loaded
unsigned int size(void)
{
    if(loaded){
        return words;
    }
    else{
        return 0;
    }
}

// Returns true if word is in dictionary else false
bool check(const char *word){


    // since word is a const char, it cannot be manipulated. therefore, we need to create a copy of it
    int word_length = strlen(word);
    char word_copy[word_length + 1];

    // before we make sure if the word is in the dictionary, we need to make every character of the word lower-case
    for(int i = 0; i < word_length; i++){
        word_copy[i] = tolower(word[i]);
    }

    word_copy[word_length] = '\0';

    // in order to search words in the dictionary, we need a cursor (pointer) that allows us to access the next node
    node* pointer = hashtable[alphabetPosition(word_copy[0])];

    // while we don't reach the end
    while(pointer != NULL){

        // if we do find a word in the pointer that corresponds to a word in the text file, return true
        if(strcmp(pointer->word, word_copy) == 0){
            return true;
        }

        // keeps searching for the corresponding word
        pointer = pointer->next;

    }



    return false;
}

// Unloads dictionary from memory, returning true if successful else false
bool unload(void)
{
    for(int i = 0; i < N; i++){
        while(hashtable[i] != NULL){
            node *tmp = hashtable[i]->next;
            free(hashtable[i]);
            hashtable[i] = tmp;
        }
    }
    return true;
}


int alphabetPosition(char firstLetter){
    for(int i = 0, n = strlen(alphabet); i < n; i++){
        if(firstLetter == alphabet[i]){
            return i;
        }
    }
    printf("error: could not get alphabetic position of the word.");
    return -1;
}
