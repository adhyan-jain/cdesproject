// Independent reference model of a scoped symbol table. Deliberately simple and built
// only from the standard library; it shares no code with any table under test.
#ifndef CDES_REFERENCE_MODEL_HPP
#define CDES_REFERENCE_MODEL_HPP

#include <cstdint>
#include <map>
#include <string>
#include <utility>
#include <vector>

class ReferenceModel {
    struct Decl { size_t depth; int32_t value; uint8_t type; };
    std::map<std::string, std::vector<Decl> > names_;
    std::vector<std::vector<std::string> > scopes_;
    size_t live_;

public:
    ReferenceModel() : scopes_(1), live_(0) {}
    void enter() { scopes_.push_back(std::vector<std::string>()); }
    bool exit() {
        if (scopes_.size() == 1) return false;
        for (size_t i = 0; i < scopes_.back().size(); ++i) {
            std::map<std::string, std::vector<Decl> >::iterator it = names_.find(scopes_.back()[i]);
            it->second.pop_back();
            if (it->second.empty()) names_.erase(it);
            --live_;
        }
        scopes_.pop_back();
        return true;
    }
    // 0 = new declaration, 1 = redeclared in the same scope (value replaced)
    int declare(const std::string& name, int32_t value, uint8_t type = 0) {
        std::vector<Decl>& v = names_[name];
        size_t depth = scopes_.size() - 1;
        if (!v.empty() && v.back().depth == depth) {
            v.back().value = value;
            v.back().type = type;
            return 1;
        }
        Decl d = {depth, value, type};
        v.push_back(d);
        scopes_.back().push_back(name);
        ++live_;
        return 0;
    }
    bool resolve(const std::string& name, int32_t* value = 0, uint8_t* type = 0) const {
        std::map<std::string, std::vector<Decl> >::const_iterator it = names_.find(name);
        if (it == names_.end()) return false;
        if (value) *value = it->second.back().value;
        if (type) *type = it->second.back().type;
        return true;
    }
    size_t live() const { return live_; }
    size_t distinct() const { return names_.size(); }
    size_t depth() const { return scopes_.size() - 1; }
};

#endif
