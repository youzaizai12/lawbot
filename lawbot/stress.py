# stress_test_separate.py - 修复ZeroDivisionError
import requests
import time
import threading
import statistics
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import sys
import random

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 配置
BASE_URL = "http://127.0.0.1:5004"

# 测试问题库
TEST_QUESTIONS = [
    "公司拖欠工资3个月，我该怎么维权？需要准备什么证据？",
    "朋友借了8万不还，有借条和转账记录，起诉流程是什么？",
    "离婚时婚后买的房子怎么分割？贷款没还完怎么办？",
    "工伤认定需要什么材料？公司不配合申请怎么办？",
    "交通事故对方全责但拒绝赔偿，我应该起诉谁？",
    "劳动合同法第39条、40条、41条有什么区别？",
    "民间借贷超过LPR四倍的利息法律支持吗？",
    "离婚诉讼中夫妻共同债务怎么认定？",
    "帮信罪中'明知'的认定标准是什么？",
    "交通事故交强险和商业险的赔付顺序是什么？",
    "公司违法辞退怎么要赔偿金？",
    "借条怎么写才有法律效力？",
    "取保候审的条件是什么？",
    "家暴怎么申请人身保护令？",
    "二手房卖家违约不卖了怎么办？",
]


class StressTester:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.results = []
        self.lock = threading.Lock()

    def test_single_request(self, user_msg, request_id, mode="normal"):
        start_time = time.time()
        url = f"{self.base_url}/chat" if mode == "normal" else f"{self.base_url}/chat-pro"

        payload = {"msg": user_msg, "context": []}

        try:
            response = requests.post(url, json=payload, timeout=120)
            end_time = time.time()
            response_time = end_time - start_time

            if response.status_code == 200:
                return {"id": request_id, "success": True, "response_time": response_time, "error": None}
            else:
                return {"id": request_id, "success": False, "response_time": response_time,
                        "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"id": request_id, "success": False, "response_time": time.time() - start_time, "error": str(e)[:50]}

    def _worker(self, request_id, user_msg, mode):
        result = self.test_single_request(user_msg, request_id, mode)
        with self.lock:
            self.results.append(result)

    # ==================== 测试1：阶梯压力测试 ====================
    def test_load_ramp(self, max_concurrency=100, step=10, requests_per_step=50, mode="normal"):
        print("\n" + "=" * 60)
        print("📈 阶梯压力测试")
        print("=" * 60)
        print(f"并发范围: 1 → {max_concurrency} (步长{step})")

        load_results = []

        for concurrency in range(1, max_concurrency + 1, step):
            print(f"  测试并发: {concurrency}")
            self.results = []
            threads = []
            questions = [random.choice(TEST_QUESTIONS) for _ in range(requests_per_step)]

            start_time = time.time()
            for i, q in enumerate(questions):
                while len([t for t in threads if t.is_alive()]) >= concurrency:
                    time.sleep(0.02)
                    threads = [t for t in threads if t.is_alive()]
                t = threading.Thread(target=self._worker, args=(i, q, mode))
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

            duration = time.time() - start_time
            success_count = len([r for r in self.results if r["success"]])
            success_times = [r["response_time"] for r in self.results if r["success"]]

            result = {
                "concurrency": concurrency,
                "total": len(self.results),
                "success_rate": success_count / len(self.results) * 100 if self.results else 0,
                "avg_response": statistics.mean(success_times) if success_times else 0,
                "p95": statistics.quantiles(success_times, n=100)[94] if len(success_times) >= 100 else (
                    statistics.mean(success_times) if success_times else 0),
                "qps": len(self.results) / duration if duration > 0 else 0
            }
            load_results.append(result)
            print(
                f"     成功率: {result['success_rate']:.1f}% | 平均响应: {result['avg_response']:.2f}s | QPS: {result['qps']:.1f}")

        return load_results

    # ==================== 测试2：极限并发测试 ====================
    def test_extreme_load(self, concurrency_list=[20, 40, 60, 80, 100, 120], requests_per_level=80, mode="normal"):
        print("\n" + "=" * 60)
        print("🔥 极限并发测试")
        print("=" * 60)
        print(f"并发级别: {concurrency_list}")

        extreme_results = []

        for concurrency in concurrency_list:
            print(f"  测试并发: {concurrency}")
            self.results = []
            threads = []
            questions = [random.choice(TEST_QUESTIONS) for _ in range(requests_per_level)]

            start_time = time.time()
            for i, q in enumerate(questions):
                while len([t for t in threads if t.is_alive()]) >= concurrency:
                    time.sleep(0.02)
                    threads = [t for t in threads if t.is_alive()]
                t = threading.Thread(target=self._worker, args=(i, q, mode))
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

            duration = time.time() - start_time
            success_count = len([r for r in self.results if r["success"]])
            success_times = [r["response_time"] for r in self.results if r["success"]]

            result = {
                "concurrency": concurrency,
                "total": len(self.results),
                "success_rate": success_count / len(self.results) * 100 if self.results else 0,
                "avg_response": statistics.mean(success_times) if success_times else 0,
                "p95": statistics.quantiles(success_times, n=100)[94] if len(success_times) >= 100 else (
                    statistics.mean(success_times) if success_times else 0),
                "qps": len(self.results) / duration if duration > 0 else 0
            }
            extreme_results.append(result)
            print(
                f"     成功率: {result['success_rate']:.1f}% | 平均响应: {result['avg_response']:.2f}s | QPS: {result['qps']:.1f}")

        return extreme_results

    # ==================== 测试3：稳定性测试（修复除零错误）====================
    def test_stability(self, duration_seconds=60, concurrency=20, mode="normal"):
        print("\n" + "=" * 60)
        print("🏃 稳定性测试")
        print("=" * 60)
        print(f"测试时长: {duration_seconds}秒 | 并发数: {concurrency}")

        self.results = []
        stop_flag = threading.Event()
        request_id = [0]

        def worker():
            while not stop_flag.is_set():
                q = random.choice(TEST_QUESTIONS)
                with self.lock:
                    rid = request_id[0]
                    request_id[0] += 1
                result = self.test_single_request(q, rid, mode)
                with self.lock:
                    result["_time"] = time.time()
                    self.results.append(result)

        threads = []
        for _ in range(concurrency):
            t = threading.Thread(target=worker)
            t.start()
            threads.append(t)

        start_time = time.time()
        for remaining in range(duration_seconds, 0, -1):
            elapsed = time.time() - start_time
            # 修复：避免除零错误
            current_qps = len(self.results) / elapsed if elapsed > 0 else 0
            sys.stdout.write(f"\r  剩余: {remaining:3d}秒 | 请求: {len(self.results):4d} | QPS: {current_qps:.1f}")
            sys.stdout.flush()
            time.sleep(1)

        stop_flag.set()
        for t in threads:
            t.join()
        print()

        success_results = [r for r in self.results if r["success"]]
        success_times = [r["response_time"] for r in success_results]

        # 按秒统计
        second_stats = []
        if self.results:
            start_t = self.results[0].get("_time", start_time)
            for sec in range(min(60, duration_seconds)):
                sec_start = start_t + sec
                sec_end = sec_start + 1
                reqs = [r for r in self.results if sec_start <= r.get("_time", 0) < sec_end]
                if reqs:
                    second_stats.append({
                        "second": sec,
                        "total": len(reqs),
                        "success": len([r for r in reqs if r["success"]])
                    })

        stability_result = {
            "duration": duration_seconds,
            "total": len(self.results),
            "success_rate": len(success_results) / len(self.results) * 100 if self.results else 0,
            "avg_response": statistics.mean(success_times) if success_times else 0,
            "qps": len(self.results) / duration_seconds if duration_seconds > 0 else 0,
            "second_stats": second_stats
        }

        print(
            f"\n  总请求: {stability_result['total']} | 成功率: {stability_result['success_rate']:.1f}% | QPS: {stability_result['qps']:.1f}")
        return stability_result


# ==================== 6张独立图表绘制函数 ====================

def draw_chart_1_qps(load_results):
    """图表1：阶梯压力测试 - QPS变化曲线"""
    plt.figure(figsize=(10, 6))
    concurrencies = [r["concurrency"] for r in load_results]
    qps_values = [r["qps"] for r in load_results]

    plt.plot(concurrencies, qps_values, 'o-', color='#3498db', linewidth=2, markersize=8)
    plt.fill_between(concurrencies, qps_values, alpha=0.3, color='#3498db')
    plt.xlabel('并发数', fontsize=12)
    plt.ylabel('QPS (请求/秒)', fontsize=12)
    plt.title('阶梯压力测试 - QPS变化曲线', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    filename = f"chart1_qps_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(filename, dpi=150)
    print(f"✅ 图表1已保存: {filename}")
    plt.show()
    return filename


def draw_chart_2_response_time(load_results):
    """图表2：阶梯压力测试 - 响应时间变化曲线"""
    plt.figure(figsize=(10, 6))
    concurrencies = [r["concurrency"] for r in load_results]
    avg_times = [r["avg_response"] for r in load_results]
    p95_times = [r["p95"] for r in load_results]

    plt.plot(concurrencies, avg_times, 's-', color='#e74c3c', linewidth=2, markersize=8, label='平均响应时间')
    plt.plot(concurrencies, p95_times, 'd--', color='#f39c12', linewidth=2, markersize=6, label='P95响应时间')
    plt.xlabel('并发数', fontsize=12)
    plt.ylabel('响应时间 (秒)', fontsize=12)
    plt.title('阶梯压力测试 - 响应时间变化曲线', fontsize=14, fontweight='bold')
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    filename = f"chart2_response_time_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(filename, dpi=150)
    print(f"✅ 图表2已保存: {filename}")
    plt.show()
    return filename


def draw_chart_3_success_rate(load_results):
    """图表3：阶梯压力测试 - 成功率变化曲线"""
    plt.figure(figsize=(10, 6))
    concurrencies = [r["concurrency"] for r in load_results]
    success_rates = [r["success_rate"] for r in load_results]

    plt.plot(concurrencies, success_rates, '^-', color='#2ecc71', linewidth=2, markersize=8)
    plt.axhline(y=99, color='green', linestyle='--', linewidth=1.5, label='99% 优秀线', alpha=0.7)
    plt.axhline(y=95, color='orange', linestyle='--', linewidth=1.5, label='95% 良好线', alpha=0.7)
    plt.axhline(y=90, color='red', linestyle='--', linewidth=1.5, label='90% 及格线', alpha=0.7)
    plt.xlabel('并发数', fontsize=12)
    plt.ylabel('成功率 (%)', fontsize=12)
    plt.title('阶梯压力测试 - 成功率变化曲线', fontsize=14, fontweight='bold')
    plt.ylim(0, 105)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    filename = f"chart3_success_rate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(filename, dpi=150)
    print(f"✅ 图表3已保存: {filename}")
    plt.show()
    return filename


def draw_chart_4_extreme_capacity(extreme_results):
    """图表4：极限并发测试 - 系统承载能力（双轴）"""
    plt.figure(figsize=(12, 6))
    extreme_conc = [r["concurrency"] for r in extreme_results]
    extreme_success = [r["success_rate"] for r in extreme_results]
    extreme_qps = [r["qps"] for r in extreme_results]

    ax1 = plt.gca()
    bars = ax1.bar([str(c) for c in extreme_conc], extreme_success, width=0.6,
                   color='#3498db', alpha=0.7, label='成功率')
    ax1.set_xlabel('并发数', fontsize=12)
    ax1.set_ylabel('成功率 (%)', fontsize=12, color='#3498db')
    ax1.tick_params(axis='y', labelcolor='#3498db')
    ax1.set_ylim(0, 105)
    ax1.axhline(y=95, color='green', linestyle='--', linewidth=1.5, label='95%基准线', alpha=0.7)

    ax2 = ax1.twinx()
    ax2.plot(range(len(extreme_conc)), extreme_qps, 'o-', color='#e74c3c', linewidth=2, markersize=8, label='QPS')
    ax2.set_ylabel('QPS (请求/秒)', fontsize=12, color='#e74c3c')
    ax2.tick_params(axis='y', labelcolor='#e74c3c')

    ax1.set_xticks(range(len(extreme_conc)))
    ax1.set_xticklabels(extreme_conc)
    ax1.set_title('极限并发测试 - 系统承载能力', fontsize=14, fontweight='bold')

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=10)

    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()

    filename = f"chart4_extreme_capacity_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(filename, dpi=150)
    print(f"✅ 图表4已保存: {filename}")
    plt.show()
    return filename


def draw_chart_5_extreme_response(extreme_results):
    """图表5：极限并发测试 - 响应时间"""
    plt.figure(figsize=(10, 6))
    extreme_conc = [r["concurrency"] for r in extreme_results]
    extreme_avg = [r["avg_response"] for r in extreme_results]

    bars = plt.bar([str(c) for c in extreme_conc], extreme_avg, color='#9b59b6', alpha=0.7)
    for bar, avg in zip(bars, extreme_avg):
        plt.text(bar.get_x() + bar.get_width() / 2, avg + 0.1, f'{avg:.1f}s',
                 ha='center', va='bottom', fontsize=10)
    plt.xlabel('并发数', fontsize=12)
    plt.ylabel('平均响应时间 (秒)', fontsize=12)
    plt.title('极限并发测试 - 响应时间', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()

    filename = f"chart5_extreme_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(filename, dpi=150)
    print(f"✅ 图表5已保存: {filename}")
    plt.show()
    return filename


def draw_chart_6_stability(stability_result):
    """图表6：稳定性测试 - 每秒请求分布"""
    plt.figure(figsize=(12, 6))
    second_stats = stability_result.get("second_stats", [])[:60]

    if not second_stats:
        print("⚠️ 稳定性测试数据不足，无法绘制图表6")
        return None

    seconds = [s["second"] for s in second_stats]
    total_reqs = [s["total"] for s in second_stats]
    success_reqs = [s["success"] for s in second_stats]

    x = range(len(seconds))
    plt.bar(x, total_reqs, alpha=0.7, label='总请求数', color='#3498db')
    plt.bar(x, success_reqs, alpha=0.7, label='成功请求数', color='#2ecc71')
    plt.xlabel('时间 (秒)', fontsize=12)
    plt.ylabel('请求数', fontsize=12)
    plt.title('稳定性测试 - 每秒请求分布 (前60秒)', fontsize=14, fontweight='bold')
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()

    filename = f"chart6_stability_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(filename, dpi=150)
    print(f"✅ 图表6已保存: {filename}")
    plt.show()
    return filename


def print_summary_report(load_results, extreme_results, stability_result):
    """打印汇总报告"""
    print("\n" + "=" * 70)
    print("📊 压力测试汇总报告".center(66))
    print("=" * 70)

    if load_results:
        print("\n【阶梯压力测试】")
        print(f"  最大并发: {load_results[-1]['concurrency']}")
        print(f"  最大QPS: {max(r['qps'] for r in load_results):.1f}")
        print(f"  最低成功率: {min(r['success_rate'] for r in load_results):.1f}%")
        print(f"  最低平均响应: {min(r['avg_response'] for r in load_results):.2f}s")

    if extreme_results:
        print("\n【极限并发测试】")
        print(f"  最大并发: {extreme_results[-1]['concurrency']}")
        print(f"  极限QPS: {extreme_results[-1]['qps']:.1f}")
        print(f"  极限成功率: {extreme_results[-1]['success_rate']:.1f}%")

        max_stable = 0
        for r in extreme_results:
            if r["success_rate"] >= 95:
                max_stable = r["concurrency"]
        print(f"  最大稳定并发: {max_stable} (成功率≥95%)")

    if stability_result:
        print("\n【稳定性测试】")
        print(f"  总请求数: {stability_result['total']}")
        print(f"  成功率: {stability_result['success_rate']:.1f}%")
        print(f"  平均QPS: {stability_result['qps']:.1f}")
        print(f"  平均响应: {stability_result['avg_response']:.2f}s")

    print("\n" + "=" * 70)


def main():
    print("\n" + "🏛️" * 20)
    print("   法律咨询系统 - 压力测试工具")
    print("   (6张独立图表)")
    print("🏛️" * 20)

    tester = StressTester()
    print("\n检查服务连接...")
    try:
        requests.get(f"{BASE_URL}/", timeout=5)
        print("✅ 服务连接正常")
    except:
        print(f"❌ 无法连接到服务: {BASE_URL}")
        print("请先启动法律咨询系统: python app.py")
        return

    while True:
        print("\n" + "-" * 50)
        print("请选择测试模式:")
        print("1. 🚀 完整测试 (生成全部6张图表)")
        print("2. 📈 仅阶梯压力测试 (图表1-3)")
        print("3. 🔥 仅极限并发测试 (图表4-5)")
        print("4. 🏃 仅稳定性测试 (图表6)")
        print("0. ❌ 退出")
        print("-" * 50)

        choice = input("请输入选项 (0-4): ").strip()

        if choice == "0":
            print("感谢使用，再见！")
            break

        elif choice == "1":
            mode = input("测试模式 (1=普通模式, 2=专业模式, 默认1): ").strip()
            mode = "pro" if mode == "2" else "normal"

            print("\n开始完整测试...\n")

            print("[1/3] 阶梯压力测试")
            load_results = tester.test_load_ramp(max_concurrency=100, step=10, requests_per_step=50, mode=mode)

            print("\n[2/3] 极限并发测试")
            extreme_results = tester.test_extreme_load(concurrency_list=[20, 40, 60, 80, 100], requests_per_level=80,
                                                       mode=mode)

            print("\n[3/3] 稳定性测试")
            stability_result = tester.test_stability(duration_seconds=60, concurrency=20, mode=mode)

            print_summary_report(load_results, extreme_results, stability_result)

            print("\n📊 正在生成图表...\n")

            if load_results:
                draw_chart_1_qps(load_results)
                draw_chart_2_response_time(load_results)
                draw_chart_3_success_rate(load_results)

            if extreme_results:
                draw_chart_4_extreme_capacity(extreme_results)
                draw_chart_5_extreme_response(extreme_results)

            if stability_result:
                draw_chart_6_stability(stability_result)

            print("\n✅ 所有图表生成完成！")

        elif choice == "2":
            mode = input("测试模式 (1=普通模式, 2=专业模式, 默认1): ").strip()
            mode = "pro" if mode == "2" else "normal"
            max_conc = int(input("最大并发数 (默认100): ").strip() or "100")

            load_results = tester.test_load_ramp(max_concurrency=max_conc, step=10, requests_per_step=50, mode=mode)

            if load_results:
                draw_chart_1_qps(load_results)
                draw_chart_2_response_time(load_results)
                draw_chart_3_success_rate(load_results)

        elif choice == "3":
            mode = input("测试模式 (1=普通模式, 2=专业模式, 默认1): ").strip()
            mode = "pro" if mode == "2" else "normal"

            extreme_results = tester.test_extreme_load(concurrency_list=[20, 40, 60, 80, 100, 120],
                                                       requests_per_level=80, mode=mode)

            if extreme_results:
                draw_chart_4_extreme_capacity(extreme_results)
                draw_chart_5_extreme_response(extreme_results)

        elif choice == "4":
            mode = input("测试模式 (1=普通模式, 2=专业模式, 默认1): ").strip()
            mode = "pro" if mode == "2" else "normal"
            duration = int(input("测试时长(秒, 默认60): ").strip() or "60")
            concurrency = int(input("并发数(默认20): ").strip() or "20")

            stability_result = tester.test_stability(duration_seconds=duration, concurrency=concurrency, mode=mode)

            if stability_result:
                draw_chart_6_stability(stability_result)

        else:
            print("无效选项，请重新选择")


if __name__ == "__main__":
    main()