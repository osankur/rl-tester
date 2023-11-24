#include <iostream>
#include <cstring>
#include "aiger.h"

void process(aiger * spec, const char * objoutput){
    int count = 0;
    int obj_index = -1;
    for(int i = 0; i < spec->num_outputs; i++){
        if(strcmp(spec->outputs[i].name, objoutput) == 0){
            obj_index = i;
            count++;
        }
        else if (strstr(spec->outputs[i].name, "objective") == NULL){
            count++;
        }
    }
    if (obj_index<0){
        std::cerr << "Could not find output '" << objoutput << "'\n";
        exit(-1);
    }
    aiger_symbol * newoutputs = new aiger_symbol[count];
    count = 0;
    for(int i = 0; i < spec->num_outputs; i++){
        if(strcmp(spec->outputs[i].name, objoutput) == 0){
            newoutputs[count++] = spec->outputs[i];
        }
        else if (strstr(spec->outputs[i].name, "objective") == NULL){
            newoutputs[count++] = spec->outputs[i];
        }
    }
    spec->num_outputs = count;

    for(int i = 0; i <  spec->num_outputs; i++){
        spec->outputs[i] = newoutputs[i];
    }
    delete[] newoutputs;
}

int main(int argc, char ** args){
    if (argc < 4){
        std::cerr << "Usage: strip_outputs [output_name] [input.aag] [output.aag]\n";
        std::cerr << "\tRemoves all outputs whose names contain 'objective' but [output_name].\n";
        return -1;
    }
    const char * objoutput = args[1];
    const char * infile = args[2];
    const char * outfile = args[3];
    aiger* spec = aiger_init();
    const char* err = aiger_open_and_read_from_file (spec, infile);
    if (err) {
        std::cerr << (std::string("Error ") + err +
               " encountered while reading AIGER file " +
               infile);
        return -1;
    }
    process(spec, objoutput);
    return !aiger_open_and_write_to_file(spec, outfile);
}