"use client";
import { RetroGrid } from "@/shared/components/ui/retro-grid";
import { Link } from '@tanstack/react-router';

export const IndexPage: React.FC = () => {
  return (
    <div className="h-screen overflow-y-auto snap-y snap-mandatory">
      <section className="h-screen snap-start w-full flex justify-center items-center bg-white">
        <RetroGridSection />
      </section>

      {featuresData.map((feature, index) => (
        <section 
          key={index}
          className="h-screen snap-start w-full relative"
        >
          <div className="sticky top-0 h-screen w-full flex items-center justify-end bg-white dark:text-muted text-foreground">
            <div className="w-1/2 px-8 pr-40">
              <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 p-8 rounded-3xl shadow-[8px_8px_16px_rgba(0,0,0,0.08),-8px_-8px_16px_rgba(255,255,255,0.06)] dark:shadow-[8px_8px_16px_rgba(0,0,0,0.25),-8px_-8px_16px_rgba(255,255,255,0.03)]">
                <h2 className="text-xl sm:text-3xl md:text-4xl font-normal mb-6 tracking-tight bg-gradient-to-b from-green-500 via-emerald-500 to-emerald-600 bg-clip-text text-transparent">
                  {feature.text}
                </h2>
                {feature.description && (
                  <p className="text-slate-500 dark:text-slate-400 text-sm md:text-base leading-relaxed border-l-2 border-emerald-500 dark:border-emerald-600 pl-4">
                    {feature.description}
                  </p>
                )}
                <div className="mt-6 text-right">
                  <Link 
                    to={feature.link || '#'}
                    className={`${!feature.link ? 'cursor-not-allowed' : ''}`}
                    onClick={(e) => !feature.link && e.preventDefault()}
                  >
                    <button
                      className="bg-emerald-500 hover:bg-emerald-600 dark:bg-emerald-600 dark:hover:bg-emerald-700 text-white font-semibold py-2 px-6 rounded-lg shadow-md hover:shadow-lg transition duration-300 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                      disabled={!feature.link}
                    >
                      {feature.button}
                    </button>
                  </Link>
                </div>
              </div>
            </div>
          </div>
          <div className="absolute inset-0 w-1/2 flex justify-center items-center z-10 pointer-events-none">
            <div className="w-32 h-32 sm:w-72 sm:h-72 md:w-80 md:h-80 pointer-events-auto">
              <img
                src={feature.image}
                alt={feature.title}
                className="w-full h-full object-cover"
              />
            </div>
          </div>
        </section>
      ))}
    </div>
  );
}

export function RetroGridSection() {
  return (
    <div className="relative flex h-full w-full flex-col items-center justify-center overflow-hidden rounded-lg ">
      <span className="pointer-events-none z-10 whitespace-pre-wrap bg-gradient-to-b from-green-400 via-green-500 to-green-600 bg-clip-text text-center text-8xl font-black leading-none tracking-tighter text-transparent filter drop-shadow-2xl">
        SafeDefi by BlockTeam
      </span>
      <RetroGrid />
    </div>
  );
}

const featuresData = [
  {
    image: "/src/shared/assets/addtofollow.png",
    title: "add to follow icon",
    text: "Отслеживание смарт-контрактов на изменения",
    description: "Будьте всегда в курсе изменений в смарт-контрактах. Наше приложение позволяет в реальном времени отслеживать любые обновления, от мелких правок до серьёзных модификаций кода. Получайте полные уведомления об изменениях структуры, логики и состояния, чтобы быстро реагировать, проводить аудит и защищать свои интересы. Всё максимально понятно и удобно!",
    link: "/contracts",
    button: "Добавить в отслеживание",
  },
  {
    image: "/src/shared/assets/audit.png",
    title: "audit icon",
    text: "Проверка смарт-контрактов на уязвимости",
    description: "Убедитесь в безопасности смарт-контракта. Искусственный интеллект проводит комплексный анализ на наличие уязвимостей и потенциальных угроз, используя современные методы. Проверяет код на известные уязвимости, анализирует структуру и логику.",
    link: "/audit",
    button: "Провести аудит",
  },
  {
    image: "/src/shared/assets/visualise.png",
    title: "visualise icon",
    text: "Визуализация смарт-контрактов",
    description: "Быстро разберитесь в устройстве смарт-контракта. Воспользуйтесь возможностью увидеть его в виде наглядного графа с ясным описанием. Искусственный интеллект проанализирует код, выделит важные сущности и построит визуальную карту, делая изучение даже сложных контрактов лёгким и интуитивным.",
    link: "/visualisation",
    button: "Визуализировать",
  }
];
