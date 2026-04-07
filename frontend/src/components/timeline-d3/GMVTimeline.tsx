import React, { useEffect, useRef, useState, useMemo } from 'react';
import * as d3 from 'd3';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export interface TimelineDataPoint {
  date: Date;
  gmv: number;
}

export interface MilestonePoint {
  date: Date;
  gmv: number;
  type: 'decline_start' | 'local_min' | 'local_max' | 'recovery';
  label: string;
}

interface GMVTimelineProps {
  data?: TimelineDataPoint[];
  className?: string;
  width?: number;
  height?: number;
  onMilestoneClick?: (milestone: MilestonePoint) => void;
}

/**
 * D3.js GMV 动态时间轴组件
 *
 * 功能特性：
 * - 面积图展示 GMV 趋势
 * - 环比下滑 >10% 标红
 * - 局部拐点自动吸附（里程碑节点）
 * - 悬停 Tooltip
 * - 缩放与拖拽
 */
export const GMVTimeline: React.FC<GMVTimelineProps> = ({
  data: externalData,
  className,
  width = 800,
  height = 280,
  onMilestoneClick,
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [tooltip, setTooltip] = useState<{
    visible: boolean;
    x: number;
    y: number;
    content: React.ReactNode;
  }>({ visible: false, x: 0, y: 0, content: null });

  // 如果没有外部数据，生成模拟数据
  const data = useMemo(() => {
    if (externalData && externalData.length > 0) return externalData;
    return generateMockData();
  }, [externalData]);

  // 计算环比和里程碑
  const { series, milestones } = useMemo(() => {
    const s = data.map((d, i) => {
      const prev = i > 0 ? data[i - 1].gmv : d.gmv;
      const mom = prev !== 0 ? (d.gmv - prev) / prev : 0;
      return { ...d, mom };
    });

    const ms = detectMilestones(s);
    return { series: s, milestones: ms };
  }, [data]);

  useEffect(() => {
    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const margin = { top: 20, right: 30, bottom: 40, left: 60 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    // 缩放行为
    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([1, 5])
      .extent([[0, 0], [innerWidth, innerHeight]])
      .translateExtent([[-innerWidth, 0], [innerWidth * 2, innerHeight]])
      .on('zoom', (event) => {
        const newX = event.transform.rescaleX(xScale);
        xAxisGroup.call(d3.axisBottom(newX).tickFormat(d3.timeFormat('%m/%d') as any));
        pathArea.attr('d', areaGenerator.x((d: any) => newX(d.date)));
        pathLine.attr('d', lineGenerator.x((d: any) => newX(d.date)));
        declinePoints.attr('cx', (d: any) => newX(d.date));
        milestoneGroup.selectAll<SVGCircleElement, MilestonePoint>('.milestone').attr('cx', (d) => newX(d.date));
        milestoneGroup.selectAll<SVGLineElement, MilestonePoint>('.milestone-line').attr('x1', (d) => newX(d.date)).attr('x2', (d) => newX(d.date));
      });

    svg.call(zoom as any);

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    // 渐变定义
    const defs = svg.append('defs');
    const gradient = defs
      .append('linearGradient')
      .attr('id', 'gmv-gradient')
      .attr('x1', '0%')
      .attr('y1', '0%')
      .attr('x2', '0%')
      .attr('y2', '100%');
    gradient.append('stop').attr('offset', '0%').attr('stop-color', '#3B82F6').attr('stop-opacity', 0.4);
    gradient.append('stop').attr('offset', '100%').attr('stop-color', '#3B82F6').attr('stop-opacity', 0.05);

    // 标红区域渐变
    const redGradient = defs
      .append('linearGradient')
      .attr('id', 'gmv-red-gradient')
      .attr('x1', '0%')
      .attr('y1', '0%')
      .attr('x2', '0%')
      .attr('y2', '100%');
    redGradient.append('stop').attr('offset', '0%').attr('stop-color', '#EF4444').attr('stop-opacity', 0.4);
    redGradient.append('stop').attr('offset', '100%').attr('stop-color', '#EF4444').attr('stop-opacity', 0.05);

    // 比例尺
    const xScale = d3
      .scaleTime()
      .domain(d3.extent(series, (d) => d.date) as [Date, Date])
      .range([0, innerWidth]);

    const maxGMV = d3.max(series, (d) => d.gmv) || 0;
    const yScale = d3
      .scaleLinear()
      .domain([0, maxGMV * 1.1])
      .range([innerHeight, 0]);

    // 轴
    const xAxisGroup = g
      .append('g')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(d3.axisBottom(xScale).tickFormat(d3.timeFormat('%m/%d') as any));
    xAxisGroup.selectAll('text').attr('fill', '#9CA3AF').style('font-size', '10px');
    xAxisGroup.selectAll('line, path').attr('stroke', '#E5E7EB');

    const yAxisGroup = g.append('g').call(
      d3
        .axisLeft(yScale)
        .ticks(5)
        .tickFormat((d: any) => `${(d / 10000).toFixed(0)}万` as any)
    );
    yAxisGroup.selectAll('text').attr('fill', '#9CA3AF').style('font-size', '10px');
    yAxisGroup.selectAll('line, path').attr('stroke', '#E5E7EB');

    // 网格线
    g.append('g')
      .attr('class', 'grid')
      .call(d3.axisLeft(yScale).tickSize(-innerWidth).tickFormat(() => ''))
      .selectAll('line')
      .attr('stroke', '#F3F4F6')
      .attr('stroke-dasharray', '2,2');
    g.select('.grid').select('.domain').remove();

    // 面积生成器
    const areaGenerator = d3
      .area<any>()
      .x((d) => xScale(d.date))
      .y0(innerHeight)
      .y1((d) => yScale(d.gmv))
      .curve(d3.curveMonotoneX);

    // 折线生成器
    const lineGenerator = d3
      .line<any>()
      .x((d) => xScale(d.date))
      .y((d) => yScale(d.gmv))
      .curve(d3.curveMonotoneX);

    // 绘制面积（分正常和标红区域）
    defs
      .append('clipPath')
      .attr('id', 'chart-clip')
      .append('rect')
      .attr('width', innerWidth)
      .attr('height', innerHeight);

    const pathArea = g
      .append('path')
      .datum(series)
      .attr('fill', 'url(#gmv-gradient)')
      .attr('d', areaGenerator)
      .attr('clip-path', 'url(#chart-clip)');

    const pathLine = g
      .append('path')
      .datum(series)
      .attr('fill', 'none')
      .attr('stroke', '#3B82F6')
      .attr('stroke-width', 2)
      .attr('d', lineGenerator);

    // 标红区域：环比下滑 >10% 的线段
    const declineSegments = getDeclineSegments(series);
    declineSegments.forEach((seg) => {
      g.append('path')
        .datum(seg)
        .attr('fill', 'url(#gmv-red-gradient)')
        .attr('d', areaGenerator)
        .attr('clip-path', 'url(#chart-clip)');

      g.append('path')
        .datum(seg)
        .attr('fill', 'none')
        .attr('stroke', '#EF4444')
        .attr('stroke-width', 2)
        .attr('d', lineGenerator);
    });

    // 下滑点标记
    const declinePoints = g
      .selectAll('.decline-point')
      .data(series.filter((d) => d.mom < -0.1))
      .enter()
      .append('circle')
      .attr('class', 'decline-point')
      .attr('cx', (d) => xScale(d.date))
      .attr('cy', (d) => yScale(d.gmv))
      .attr('r', 4)
      .attr('fill', '#EF4444')
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5)
      .style('cursor', 'pointer')
      .on('mouseover', (event, d) => {
        setTooltip({
          visible: true,
          x: event.clientX + 12,
          y: event.clientY - 12,
          content: (
            <div className="text-xs">
              <div className="font-medium text-red-600">GMV 显著下滑</div>
              <div className="text-gray-600 mt-1">{d3.timeFormat('%Y-%m-%d')(d.date)}</div>
              <div className="mt-1">GMV: {(d.gmv / 10000).toFixed(1)}万</div>
              <div className="text-red-600">环比: {(d.mom * 100).toFixed(1)}%</div>
            </div>
          ),
        });
      })
      .on('mousemove', (event) => {
        setTooltip((t) => ({ ...t, x: event.clientX + 12, y: event.clientY - 12 }));
      })
      .on('mouseout', () => {
        setTooltip((t) => ({ ...t, visible: false }));
      });

    // 里程碑节点
    const milestoneGroup = g.append('g').attr('class', 'milestones');

    milestoneGroup
      .selectAll('.milestone-line')
      .data(milestones)
      .enter()
      .append('line')
      .attr('class', 'milestone-line')
      .attr('x1', (d) => xScale(d.date))
      .attr('y1', (d) => yScale(d.gmv))
      .attr('x2', (d) => xScale(d.date))
      .attr('y2', innerHeight)
      .attr('stroke', (d) => (d.type === 'decline_start' ? '#EF4444' : '#10B981'))
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', '3,3')
      .style('opacity', 0.5);

    milestoneGroup
      .selectAll('.milestone')
      .data(milestones)
      .enter()
      .append('circle')
      .attr('class', 'milestone')
      .attr('cx', (d) => xScale(d.date))
      .attr('cy', (d) => yScale(d.gmv))
      .attr('r', 6)
      .attr('fill', (d) => (d.type === 'decline_start' ? '#EF4444' : d.type === 'local_min' ? '#F59E0B' : '#10B981'))
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .on('mouseover', (event, d) => {
        setTooltip({
          visible: true,
          x: event.clientX + 12,
          y: event.clientY - 12,
          content: (
            <div className="text-xs">
              <div className="font-medium">{d.label}</div>
              <div className="text-gray-600 mt-1">{d3.timeFormat('%Y-%m-%d')(d.date)}</div>
              <div className="mt-1">GMV: {(d.gmv / 10000).toFixed(1)}万</div>
            </div>
          ),
        });
      })
      .on('mousemove', (event) => {
        setTooltip((t) => ({ ...t, x: event.clientX + 12, y: event.clientY - 12 }));
      })
      .on('mouseout', () => {
        setTooltip((t) => ({ ...t, visible: false }));
      })
      .on('click', (_event, d) => {
        onMilestoneClick?.(d);
      });

    // 里程碑标签
    milestoneGroup
      .selectAll('.milestone-label')
      .data(milestones)
      .enter()
      .append('text')
      .attr('class', 'milestone-label')
      .attr('x', (d) => xScale(d.date))
      .attr('y', (d) => yScale(d.gmv) - 12)
      .attr('text-anchor', 'middle')
      .style('font-size', '10px')
      .style('font-weight', '500')
      .style('fill', '#4B5563')
      .style('pointer-events', 'none')
      .text((d) => d.label);

    // 交互覆盖层（捕捉鼠标位置显示当前值）
    const overlay = g
      .append('rect')
      .attr('width', innerWidth)
      .attr('height', innerHeight)
      .style('fill', 'none')
      .style('pointer-events', 'all');

    const focusLine = g.append('line').style('opacity', 0).attr('stroke', '#9CA3AF').attr('stroke-dasharray', '3,3').attr('y1', 0).attr('y2', innerHeight);
    const focusCircle = g.append('circle').style('opacity', 0).attr('r', 4).attr('fill', '#3B82F6').attr('stroke', '#fff').attr('stroke-width', 2);

    overlay
      .on('mousemove', (event) => {
        const [mx] = d3.pointer(event);
        const hoveredDate = xScale.invert(mx);
        const bisect = d3.bisector((d: any) => d.date).left;
        const i = bisect(series, hoveredDate, 1);
        const d0 = series[i - 1];
        const d1 = series[i];
        if (!d0 || !d1) return;
        const d = hoveredDate.valueOf() - d0.date.valueOf() > d1.date.valueOf() - hoveredDate.valueOf() ? d1 : d0;

        focusLine.style('opacity', 1).attr('x1', xScale(d.date)).attr('x2', xScale(d.date));
        focusCircle.style('opacity', 1).attr('cx', xScale(d.date)).attr('cy', yScale(d.gmv));

        setTooltip({
          visible: true,
          x: event.sourceEvent.clientX + 12,
          y: event.sourceEvent.clientY - 12,
          content: (
            <div className="text-xs">
              <div className="font-medium text-gray-900">{d3.timeFormat('%Y-%m-%d')(d.date)}</div>
              <div className="mt-1">GMV: {(d.gmv / 10000).toFixed(1)}万</div>
              <div className={d.mom < 0 ? 'text-red-600' : 'text-green-600'}>环比: {(d.mom * 100).toFixed(1)}%</div>
            </div>
          ),
        });
      })
      .on('mouseout', () => {
        focusLine.style('opacity', 0);
        focusCircle.style('opacity', 0);
        setTooltip((t) => ({ ...t, visible: false }));
      });
  }, [series, milestones, width, height, onMilestoneClick]);

  return (
    <div ref={containerRef} className={cn('relative', className)}>
      <svg ref={svgRef} width={width} height={height} className="block" />

      {/* Tooltip */}
      {tooltip.visible && (
        <div
          className="fixed z-50 px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg shadow-lg pointer-events-none"
          style={{ left: tooltip.x, top: tooltip.y }}
        >
          {tooltip.content}
        </div>
      )}
    </div>
  );
};

// ============ 辅助函数 ============

function generateMockData(): TimelineDataPoint[] {
  const data: TimelineDataPoint[] = [];
  const startDate = new Date('2026-01-01');
  const baseGMV = 350000;

  for (let i = 0; i < 90; i++) {
    const date = new Date(startDate);
    date.setDate(date.getDate() + i);

    // 模拟季节性 + 下滑 + 恢复
    let factor = 1;
    if (i > 30 && i < 50) {
      // 下滑期
      factor -= (i - 30) * 0.015;
    } else if (i >= 50 && i < 60) {
      // 底部
      factor -= 0.3;
    } else if (i >= 60) {
      // 恢复期
      factor -= 0.3 - (i - 60) * 0.008;
    }

    // 周末波动
    const weekendFactor = date.getDay() === 0 || date.getDay() === 6 ? 0.85 : 1.05;
    const noise = 0.95 + Math.random() * 0.1;
    const gmv = Math.max(100000, baseGMV * factor * weekendFactor * noise);

    data.push({ date, gmv });
  }

  return data;
}

function getDeclineSegments(series: (TimelineDataPoint & { mom: number })[]): (TimelineDataPoint & { mom: number })[][] {
  const segments: (TimelineDataPoint & { mom: number })[][] = [];
  let current: (TimelineDataPoint & { mom: number })[] = [];

  for (let i = 0; i < series.length; i++) {
    if (series[i].mom < -0.1) {
      current.push(series[i]);
    } else {
      if (current.length > 0) {
        // 包含前后各一个点使线段连续
        const startIdx = Math.max(0, series.indexOf(current[0]) - 1);
        const endIdx = Math.min(series.length - 1, series.indexOf(current[current.length - 1]) + 1);
        segments.push(series.slice(startIdx, endIdx + 1));
        current = [];
      }
    }
  }

  if (current.length > 0) {
    const startIdx = Math.max(0, series.indexOf(current[0]) - 1);
    segments.push(series.slice(startIdx));
  }

  return segments;
}

function detectMilestones(series: (TimelineDataPoint & { mom: number })[]): MilestonePoint[] {
  const milestones: MilestonePoint[] = [];
  if (series.length < 5) return milestones;

  // 1. 下滑起点：环比首次 < -10%
  const firstDecline = series.findIndex((d) => d.mom < -0.1);
  if (firstDecline > 0) {
    milestones.push({
      date: series[firstDecline].date,
      gmv: series[firstDecline].gmv,
      type: 'decline_start',
      label: '下滑起点',
    });
  }

  // 2. 局部拐点检测（滑动窗口）
  const windowSize = 5;
  for (let i = windowSize; i < series.length - windowSize; i++) {
    const left = series.slice(i - windowSize, i);
    const right = series.slice(i + 1, i + windowSize + 1);
    const current = series[i];

    const leftAvg = d3.mean(left, (d) => d.gmv) || 0;
    const rightAvg = d3.mean(right, (d) => d.gmv) || 0;

    // 局部最小值
    if (current.gmv < leftAvg && current.gmv < rightAvg && current.gmv < series[i - 1].gmv && current.gmv < series[i + 1].gmv) {
      // 避免过密
      const last = milestones[milestones.length - 1];
      if (!last || current.date.getTime() - last.date.getTime() > 3 * 24 * 60 * 60 * 1000) {
        milestones.push({
          date: current.date,
          gmv: current.gmv,
          type: 'local_min',
          label: '局部低点',
        });
      }
    }

    // 局部最大值（恢复期）
    if (current.gmv > leftAvg && current.gmv > rightAvg && current.gmv > series[i - 1].gmv && current.gmv > series[i + 1].gmv) {
      const last = milestones[milestones.length - 1];
      if (!last || current.date.getTime() - last.date.getTime() > 3 * 24 * 60 * 60 * 1000) {
        milestones.push({
          date: current.date,
          gmv: current.gmv,
          type: 'local_max',
          label: '恢复高点',
        });
      }
    }
  }

  // 3. 恢复期：连续 5 天环比 > 0 且累计回升 > 5%
  let positiveStreak = 0;
  let streakStart = -1;
  for (let i = firstDecline > 0 ? firstDecline : 0; i < series.length; i++) {
    if (series[i].mom > 0) {
      if (positiveStreak === 0) streakStart = i;
      positiveStreak++;
      if (positiveStreak === 5 && streakStart > 0) {
        const recoveryRate = (series[i].gmv - series[streakStart].gmv) / series[streakStart].gmv;
        if (recoveryRate > 0.05) {
          milestones.push({
            date: series[i].date,
            gmv: series[i].gmv,
            type: 'recovery',
            label: '趋势恢复',
          });
        }
      }
    } else {
      positiveStreak = 0;
    }
  }

  return milestones;
}
