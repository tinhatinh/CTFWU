#ifndef AUTH_HH
#define AUTH_HH

#include <iostream>
#include <fstream>
#include <cstring>
#include "session.hh"

#include <dlfcn.h>

extern "C" void shim_flush_class(size_t);

namespace sat::client
{
   using flush_class_fn = void(*)(size_t);
   inline void maybe_flush_shim_class(size_t n)
   {
      static flush_class_fn fn = reinterpret_cast<flush_class_fn>(
         dlsym(RTLD_DEFAULT, "shim_flush_class"));
      if (fn) fn(n);
   }
   
   struct auth_sess
   {
      char head[24];
      void (*dbg)(session&); // sizeof(ptr) on 64 bit systems?
      char tail[32];
   };
   
   void contrivance(session& s)
   {
      // contrivances extraordinaire
      auth_sess* dbg_sess = (auth_sess*)malloc(sizeof(auth_sess));
      auth_sess* dbg_ses2 = (auth_sess*)malloc(sizeof(auth_sess));
      asm volatile("" : : "r"(dbg_sess), "r"(dbg_ses2) : "memory");
      free(dbg_sess);
      free(dbg_ses2);
      free(dbg_sess);
   }

   inline int hexval(char c)
   {
      if (c >= '0' && c <= '9') return c - '0';
      if (c >= 'a' && c <= 'f') return c - 'a' + 10;
      if (c >= 'A' && c <= 'F') return c - 'A' + 10;
      return -1;
   }

   inline char* get_password()
   {
      char* password = (char*)malloc(64);
      memset(password, 0, 64);

      std::cout << "Enter password (hex-encoded): ";

      char hexbuf[129];
      memset(hexbuf, 0, sizeof(hexbuf));
      std::cin.getline(hexbuf, sizeof(hexbuf));

      size_t hexlen = strlen(hexbuf);
      size_t n = hexlen / 2;
      if (n > 64) n = 64;

      for (size_t i = 0; i < n; i++)
      {
	 int hi = hexval(hexbuf[i * 2]);
	 int lo = hexval(hexbuf[i * 2 + 1]);
	 if (hi < 0 || lo < 0) break;
	 password[i] = (char)((hi << 4) | lo);
      }

      return password;
   }
   
   inline bool check_password(char* password, session& s)
   {
      // set up auth sess
      bool result{false};
      char* dummy = (char*)malloc(64);
      memset(dummy, 0, 64);
      auth_sess* real_auth_sess = (auth_sess*)malloc(sizeof(auth_sess));
      if (real_auth_sess->dbg != NULL)
      {
	 real_auth_sess->dbg(s);
      }
      
      // get flag from /flag.txt
      char* flag = (char*)malloc(96);
      memset(flag, 0, 96);
      std::ifstream flag_file("/flag.txt");
      flag_file.getline(flag, 96);

      // compare
      if (strlen(flag) == strlen(password) && !strncmp(password, flag, strlen(flag)))
      {
	 result = true;
      }
      free(password);
      free(flag);
      free(dummy);
      maybe_flush_shim_class(sizeof(auth_sess));
      return result || s.authed;
   }
}

#endif /* AUTH_HH */
