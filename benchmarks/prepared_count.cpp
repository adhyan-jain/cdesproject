// Instructions for one replay with names packed and hashed on every call (plain) and with
// names prepared once before the replay (prepared), for STRATA and the stored-hash table.
//   prepared_count TRACE LABEL
#define CDES_DEFINE_NEW
#include <linux/perf_event.h>
#include <sys/ioctl.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <memory>
#include "baselines/tables.hpp"
static int fi;
template<class T,class P> static uint64_t go(const Trace&tr,bool prep){
  std::vector<P> ps(tr.names.size());
  std::unique_ptr<T> t(new T());
  if(prep) for(size_t i=0;i<tr.names.size();++i) t->prep(tr.names[i],ps[i]);
  ioctl(fi,PERF_EVENT_IOC_RESET,0);ioctl(fi,PERF_EVENT_IOC_ENABLE,0);
  int32_t seq=0,sink=0;
  for(size_t i=0;i<tr.ops.size();++i){const Op&op=tr.ops[i];
   switch(op.kind){case OP_ENTER:t->enter();break;case OP_EXIT:t->exit();break;
   case OP_DECLARE: sink+= prep? t->declare_p(ps[op.name],seq++) : t->declare(tr.names[op.name],seq++); break;
   case OP_LOOKUP:{int32_t v=0; sink+= prep? (t->resolve_p(ps[op.name],&v)?v:0) : (t->resolve(tr.names[op.name],&v)?v:0); break;}
   default:t.reset(new T());seq=0;}}
  ioctl(fi,PERF_EVENT_IOC_DISABLE,0); static volatile int32_t g; g=sink; uint64_t v=0;(void)!read(fi,&v,8); return v;}
struct S1{ tables::Strata s; strata::Key dummy;
  void enter(){s.enter();} void exit(){s.exit();}
  void prep(const std::string&n,strata::Key&k){s.t.make_key(n.data(),n.size(),k);}
  int declare(const std::string&n,int32_t v){return s.declare(n,v);} bool resolve(const std::string&n,int32_t*v){return s.resolve(n,v);}
  int declare_p(const strata::Key&k,int32_t v){return s.t.declare(k,v);} bool resolve_p(const strata::Key&k,int32_t*v){return s.t.resolve(k,v);} };
struct C0{ tables::ArenaChain c;
  bool enter(){return c.enter();} bool exit(){return c.exit();}
  void prep(const std::string&n,arena_chain::Table::Prep&p){c.t.prepare(n.data(),n.size(),p);}
  int declare(const std::string&n,int32_t v){return c.declare(n,v);} bool resolve(const std::string&n,int32_t*v){return c.resolve(n,v);}
  int declare_p(const arena_chain::Table::Prep&p,int32_t v){return c.t.declare(p,v);} bool resolve_p(const arena_chain::Table::Prep&p,int32_t*v){return c.t.resolve(p,v);} };
int main(int,char**v){Trace tr;load_trace(v[1],tr);
 perf_event_attr a;memset(&a,0,sizeof a);a.type=PERF_TYPE_HARDWARE;a.size=sizeof a;a.config=PERF_COUNT_HW_INSTRUCTIONS;a.exclude_kernel=1;a.exclude_hv=1;a.disabled=1;
 fi=syscall(__NR_perf_event_open,&a,0,-1,-1,0);
 double s0=go<S1,strata::Key>(tr,false)/1e6,s1=go<S1,strata::Key>(tr,true)/1e6,c0=go<C0,arena_chain::Table::Prep>(tr,false)/1e6,c1=go<C0,arena_chain::Table::Prep>(tr,true)/1e6;
 printf("%-9s strata %.2f -> prepared %.2f | c0 %.2f -> prepared %.2f | ratio plain %.2f prepared %.2f\n",v[2],s0,s1,c0,c1,s0/c0,s1/c1);}
