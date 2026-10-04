#ifndef CMD_AUTH_HH
#define CMD_AUTH_HH

#include <iostream>
#include <sstream>
#include "session.hh"
#include "auth.hh"

namespace sat::client::cmd
{
   void auth_bypass_dbg(session& s)
   {
      s.authed = true;
      std::cout << "auth forced via dbg";
   }
   
   inline void authenticate(session& s, std::istringstream&)
   {
      if (s.authed)
      {
         std::cout << "already authenticated\n";
         return;
      }
      contrivance(s);
      char* password = get_password();
      s.authed = check_password(password, s);
      std::cout << (s.authed ? "authenticated\n" : "authentication failed\n");
   }
}

#endif /* CMD_AUTH_HH */
