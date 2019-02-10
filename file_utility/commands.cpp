// $Id: commands.cpp,v 1.17 2018-01-25 14:02:55-08 - - $

// command functions for assignment 2

#include "commands.h"
#include "debug.h"
#include "file_sys.h"

/////////////////////////////////////////////////////////////////
// commands.cpp
/////////////////////////////////////////////////////////////////

command_hash cmd_hash {
   {"cat"   , fn_cat   },
   {"cd"    , fn_cd    },
   {"echo"  , fn_echo  },
   {"exit"  , fn_exit  },
   {"ls"    , fn_ls    },
   {"lsr"   , fn_lsr   },
   {"make"  , fn_make  },
   {"mkdir" , fn_mkdir },
   {"prompt", fn_prompt},
   {"pwd"   , fn_pwd   },
   {"rm"    , fn_rm    },
};

command_fn find_command_fn (const string& cmd) {
   // Note: value_type is pair<const key_type, mapped_type>
   // So: iterator->first is key_type (string)
   // So: iterator->second is mapped_type (command_fn)

   DEBUGF ('c', "[" << cmd << "]");
   const auto result = cmd_hash.find (cmd);
   if (result == cmd_hash.end()) {
      throw command_error (cmd + ": no such function");
   }
   return result->second; // return function
}

command_error::command_error (const string& what):
            runtime_error (what) {
}

int exit_status_message() {
   int exit_status = exit_status::get();
   cout << execname() << ": exit(" << exit_status << ")" << endl;
   return exit_status;
}

// functions ----------------------------------------------------------------
// inode_state state originally comes to function as empty package
// check if state has null root

void fn_cat (inode_state& state, const wordvec& words){ // incomplete
   DEBUGF ('c', state);
   DEBUGF ('c', words);
   // print file contents
   if (words.size() < 2){
      throw file_error ("no file or directory specified");
   }

   for (unsigned int i=1; i<words.size(); i++){
      string file_name = words.at(i);
      // seach cwd for file name, get base_file_ptr then call readfile()
      base_file_ptr file = state.get_cwd()->find_file(file_name);
      if (file == nullptr){
         cerr << "cat: " << words.at(1) << ": No such file or directory" << endl;
         cout << "yshell: exit(1)" << endl;
         exit(1);

         // probably threw an exception
      }
      else {
         file->readfile();
      }
   }
}

void fn_cd (inode_state& state, const wordvec& words){ // incomplete
   DEBUGF ('c', state);
   DEBUGF ('c', words);

   if (words.size() < 2){
      // set cwd to root
      state.set_cwd(state.get_root());
   }
   else if (words.at(1) == ".."){
      state.set_cwd(state.get_cwd()->get_parent());
   }
   else if (words.at(1) == "/"){
      state.set_cwd(state.get_root());
   }
   else { // search for given directory

      string request_dir = words.at(1);
      base_file_ptr found = state.get_cwd()->r_find(request_dir);
      if (found == nullptr){
         throw file_error ("no directory found");
      }
      state.set_cwd(found);
   }
}

void fn_echo (inode_state& state, const wordvec& words){ // already done
   DEBUGF ('c', state);
   DEBUGF ('c', words);
   cout << word_range (words.cbegin() + 1, words.cend()) << endl;
}


void fn_exit (inode_state& state, const wordvec& words){ // already done
   DEBUGF ('c', state);
   DEBUGF ('c', words);
   throw ysh_exit();
}

// all incomplete
void fn_ls (inode_state& state, const wordvec& words){
   DEBUGF ('c', state);
   DEBUGF ('c', words);
   
   if (words.size() >= 2){
      if (words.at(1) == "."){
      cout << ".:" << endl;
      }
   } 
   else{
      cout << "/:" << endl;
   }
   // print cwd info
   format(state.get_cwd()->my_num);
   cout << state.get_cwd()->my_num;
   format(state.get_cwd()->size());
   cout << state.get_cwd()->size();
   cout << "  ." << endl;

   // print parent info
   if (state.get_cwd()->title == state.get_root()->title){
      format(state.get_cwd()->my_num);
      cout << state.get_cwd()->my_num;
      format(state.get_cwd()->size());
      cout << state.get_cwd()->size();
   }
   else{
      // find parent and print parent number
      format(state.get_cwd()->get_parent()->my_num);
      cout << state.get_cwd()->get_parent()->my_num;
      format(state.get_cwd()->get_parent()->size());
      cout << state.get_cwd()->get_parent()->size();
   }
   cout << "  .." << endl;

   // if no pathname given, print cwd contents
   if (words.size() < 2 or words.at(1) == "."){
      state.get_cwd()->print_contents();
   }
   else if (state.get_root()->title == words.at(1)){ // print root
      state.get_root()->print_contents();
   }
   else if (words.at(1) == "..") // print parent
      state.get_cwd()->get_parent()->print_contents();
   else {
      base_file_ptr found = state.get_root()->r_find(words.at(1));
      found->print_contents();
   }

}

void fn_lsr (inode_state& state, const wordvec& words){ 
   DEBUGF ('c', state);
   DEBUGF ('c', words);

   if (words.size() >= 2){
      cout << "in first" << endl;
      if (words.at(1) == "/"){
         cout << words.at(1)+":" << endl;
      }
      else {
         cout << "/" << words.at(1) << endl;
      }

      string pathname = words.at(1);
      //base_file_ptr found;

      base_file_ptr found = state.get_root()->r_find(pathname);
      if (found == nullptr){
         format(state.get_root()->my_num);
         cout << state.get_root()->my_num;
         format(state.get_root()->size());
         cout << state.get_root()->size();
         cout << "  ." << endl;

         format(state.get_root()->my_num);
         cout << state.get_root()->my_num;
         format(state.get_root()->size());
         cout << state.get_root()->size();
         cout << "  .." << endl;

         string file_name = state.get_root()->title;
         state.get_root()->traverse(file_name);

      }
      else {

         // print found info
         format(found->my_num);
         cout << found->my_num;
         format(found->size());
         cout << found->size();
         cout << "  ." << endl;

         // print parent info
         format(found->get_parent()->my_num);
         cout << found->get_parent()->my_num;
         format(found->get_parent()->size());
         cout << found->get_parent()->size();
         cout << "  ..";
   
         found->traverse(found->title);
      }
   } 
   else{ // no target was specified
      cout << "/:" << endl;
      // print cwd info
      format(state.get_cwd()->my_num);
      cout << state.get_cwd()->my_num;
      format(state.get_cwd()->size());
      cout << state.get_cwd()->size();
      cout << "  ." << endl;

      // print parent info
      if (state.get_cwd()->title == state.get_root()->title){
         format(state.get_cwd()->my_num);
         cout << state.get_cwd()->my_num;
         format(state.get_cwd()->size());
         cout << state.get_cwd()->size();
         cout << "  .." << endl;

      }
      else{
         // find parent and print parent number
         format(state.get_cwd()->get_parent()->my_num);
         cout << state.get_cwd()->get_parent()->my_num;
         format(state.get_cwd()->get_parent()->size());
         cout << state.get_cwd()->get_parent()->size();
         cout << "  .." << endl;
         //cout << "pwd1 = " << state.get_cwd()->title << endl;
      }

      state.get_cwd()->print_contents();
      //cout << "pwd2 = " << state.get_cwd()->title << endl;
      string file_name = state.get_cwd()->title;
      state.get_cwd()->traverse(file_name);
      //cout << "pwd3 = " << state.get_cwd()->title << endl;
   }
   /*
   // print cwd info
   format(state.get_cwd()->my_num);
   cout << state.get_cwd()->my_num;
   format(state.get_cwd()->size());
   cout << state.get_cwd()->size();
   cout << "  ." << endl;

   // print parent info
   if (state.get_cwd()->title == state.get_root()->title){
      format(state.get_cwd()->my_num);
      cout << state.get_cwd()->my_num;
      format(state.get_cwd()->size());
      cout << state.get_cwd()->size();
   }
   else{
      // find parent and print parent number
      format(state.get_cwd()->get_parent()->my_num);
      cout << state.get_cwd()->get_parent()->my_num;
      format(state.get_cwd()->get_parent()->size());
      cout << state.get_cwd()->get_parent()->size();
   }
   cout << "  .." << endl;
   if (words.size() < 2){
      state.get_cwd()->print_contents();
      state.get_cwd()->traverse(state.get_cwd()->title);
   }
   else if (words.at(1) == "/"){
      state.get_root()->print_contents();
      state.get_root()->traverse(state.get_root()->title);
   }
   else {
      string pathname = words.at(1);
      base_file_ptr found = state.get_cwd()->r_find(pathname);
      found->traverse(found->title);
   }*/

}

void fn_make (inode_state& state, const wordvec& words){
   DEBUGF ('c', state);
   DEBUGF ('c', words);
   
   state.tree_num ++;
   string file_name = words.at(1);
   base_file_ptr new_file = state.get_cwd()->mkfile(file_name, state.tree_num);
   new_file->writefile(words); // wirte to the file
   new_file->set_parent(state.get_cwd());
}

void fn_mkdir (inode_state& state, const wordvec& words){
   DEBUGF ('c', state);
   DEBUGF ('c', words);

   state.tree_num++;
   string dir_name = words.at(1); // name of new directory
   base_file_ptr newd = state.get_cwd()->mkdir(dir_name, state.tree_num); 
   newd->set_parent(state.get_cwd()); // set parent of new dir
}

void fn_prompt (inode_state& state, const wordvec& words){ // done
   DEBUGF ('c', state);
   DEBUGF ('c', words);
   // update the prompt to the specified string
   // state.prompt = words[1-end];
   string new_prompt;
   for (unsigned int i=1; i<words.size(); i++){
      new_prompt += words[i];
   }
   new_prompt += " ";
   state.prompt_ = new_prompt; // set the new prompt
}

void fn_pwd (inode_state& state, const wordvec& words){
   DEBUGF ('c', state);
   DEBUGF ('c', words);
   // print the current working directory
   cout << state.get_cwd()->title << endl;
}

void fn_rm (inode_state& state, const wordvec& words){
   DEBUGF ('c', state);
   DEBUGF ('c', words);
   // remove file or directory
   // if directory, map must be empty
   string to_delete = words.at(1);
   state.get_cwd()->remove(to_delete);

}

void fn_rmr (inode_state& state, const wordvec& words){
   DEBUGF ('c', state);
   DEBUGF ('c', words);
   // all files in cwd are removed as well as all sub directories
}

void format(int size){
   if (size < 100){
      cout << "     ";
   }
   else if (size < 1000){
      cout << "    ";
   }
   else if (size < 10000){
      cout << "   ";
   }
   
}








