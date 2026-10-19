// Feasibility check: adaptive collision learning against the KEYED bounded table.
// Oracle = Stats::longest_probe after one extra declaration (idealised stand-in for a timing channel).
#include "strata/strata.hpp"
#include <cstdio>
#include <random>
#include <string>
#include <vector>
using namespace strata;
static std::mt19937_64 rng(12345);
static std::string rname(int len=12){ static const char*A="abcdefghijklmnopqrstuvwxyz"; std::string s; for(int i=0;i<len;i++) s+=A[rng()%26]; return s; }
static const uint32_t M=2048, L=512;
static uint32_t KEY[2];
static Options opts(){ Options o; o.index_slots=M; o.max_probe=L; o.keyed=true; o.key[0]=KEY[0]; o.key[1]=KEY[1]; return o; }
int main(){
  KEY[0]=(uint32_t)rng(); KEY[1]=(uint32_t)rng();           // secret, persistent across "compilations"
  static uint32_t buf[1<<16];
  // Phase 1 (attacker): learn names that share ONE home slot, using only the probe oracle, fresh tables, no key knowledge.
  std::string anchor="anchor_name"; std::vector<std::string> coll; unsigned long long queries=0;
  while(coll.size()<700){
    std::string c=rname(); Table t(buf,sizeof buf,opts());
    t.declare(anchor.data(),anchor.size(),1); t.declare(c.data(),c.size(),2); ++queries;
    if(t.stats().longest_probe==2) coll.push_back(c);          // c landed on anchor's home slot
  }
  std::printf("attacker learned %zu same-home names with %llu oracle queries (index has %u slots)\n",coll.size(),queries,M);
  // Phase 2 (victim compile): attacker's names first, then honest names with no collision structure.
  int refused=0, honest=1000, adv_refused=0;
  Table t(buf,sizeof buf,opts());
  t.declare(anchor.data(),anchor.size(),1);
  for(auto&c:coll) if(t.declare(c.data(),c.size(),2)==kProbeLimit) ++adv_refused;
  for(int i=0;i<honest;i++){ std::string h="honest_"+rname(10); if(t.declare(h.data(),h.size(),3)==kProbeLimit) ++refused; }
  std::printf("with attack:    adversary's own names refused: %d;  honest names refused: %d / %d  (%.1f%%)\n",adv_refused,refused,honest,100.0*refused/honest);
  // Control: same number of RANDOM attacker names.
  Table c0(buf,sizeof buf,opts()); int r0=0;
  for(size_t i=0;i<coll.size()+1;i++){ std::string x=rname(); c0.declare(x.data(),x.size(),1); }
  for(int i=0;i<honest;i++){ std::string h="honest_"+rname(10); if(c0.declare(h.data(),h.size(),3)==kProbeLimit) ++r0; }
  std::printf("control (random): honest names refused: %d / %d\n",r0,honest);
  // Mitigation: fresh key per table -> learned names are useless.
  KEY[0]=(uint32_t)rng(); KEY[1]=(uint32_t)rng();
  Table t2(buf,sizeof buf,opts()); int r2=0;
  t2.declare(anchor.data(),anchor.size(),1); for(auto&c:coll) t2.declare(c.data(),c.size(),2);
  for(int i=0;i<honest;i++){ std::string h="honest_"+rname(10); if(t2.declare(h.data(),h.size(),3)==kProbeLimit) ++r2; }
  std::printf("rekeyed table:  honest names refused: %d / %d\n",r2,honest);
}
