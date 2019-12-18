#include<iostream>
#include<fstream>
#include<string>
#include<cstring>
#include<vector>
#include<time.h>
#include<sys/time.h>

void writebinaryfile() {
    struct timeval us_start;
    gettimeofday(&us_start, NULL);
    auto fun_split = [](const std::string  & s, std::vector<std::string>& ret, const char& c) {
        size_t i = 0;
        size_t j = s.find(c);
        while (j != std::string::npos) {
            ret.push_back(s.substr(i, j - i));
            i = ++j;
            j = s.find(c, j);
        }
        if (i < s.size()) {
            ret.push_back(s.substr(i, s.size() - i));
        }
    };
    std::string str;
    std::ifstream ifs("card_history.txt");
    if(!ifs) {
        std::cout << "open file fail!" << std::endl;
        return ;
    }
    std::vector<std::vector<int>> Cards;
    while( getline(ifs, str)) {
        std::vector<std::string> ret;
        fun_split(str, ret, ',');
        if (ret.size() != 54) {
            std::cout << "--" << ret.size();
            continue;
        }

        std::vector<int> card;
        for (auto& i : ret) {
            int cardNumber = atoi(i.c_str());
            if (cardNumber < 0 || cardNumber > 53) {
                break;
            }
            card.push_back(cardNumber);
        }
        Cards.push_back(card);
    }
    ifs.close();
    struct timeval us_end;
    gettimeofday(&us_end, NULL);

    std::cout << "start:" << us_start.tv_sec << " "  << us_start.tv_usec << std::endl;
    std::cout << "end:" << us_end.tv_sec << " " << us_end.tv_usec << std::endl;
    std::cout << (us_end.tv_usec - us_start.tv_usec) / 1000 << " ms, cards size " << Cards.size() << std::endl;

    std::ofstream output( "card_history.bin", std::ios::trunc | std::ios::binary );
    for(std::size_t i = 0; i < Cards.size(); ++i) {
        output.write((char*)(&Cards[i][0]), sizeof(int) * 54);
    }
    output.close();
}

int main() {
    writebinaryfile();
    return 0;
}
